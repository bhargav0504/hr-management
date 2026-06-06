from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.bonus import BonusRecord
from app.models.payroll import SalaryRecord
from datetime import date

bonus_bp = Blueprint('bonus', __name__, url_prefix='/bonus')


def _cid():
    return session.get('company_id')


def _eligible_months(emp, fy_year):
    """Count months of service in financial year (April fy_year to March fy_year+1)."""
    fy_start = date(fy_year, 4, 1)
    fy_end = date(fy_year + 1, 3, 31)
    join = emp.date_of_joining or fy_start
    leave = emp.date_of_leaving or fy_end
    start = max(join, fy_start)
    end = min(leave, fy_end)
    if end < start:
        return 0
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    return min(max(months, 0), 12)


def _annual_basic_da(emp, fy_year):
    """Sum basic+DA from salary records in the FY, or estimate from current salary."""
    records = SalaryRecord.query.filter(
        SalaryRecord.employee_id == emp.id,
        db.or_(
            db.and_(SalaryRecord.year == fy_year, SalaryRecord.month >= 4),
            db.and_(SalaryRecord.year == fy_year + 1, SalaryRecord.month <= 3),
        )
    ).all()
    if records:
        return sum(float(r.basic or 0) + float(r.da or 0) for r in records)
    # Fallback: estimate from current salary
    monthly = float(emp.basic_salary or 0) + float(emp.da or 0)
    months = _eligible_months(emp, fy_year)
    return round(monthly * months, 2)


@bonus_bp.route('/')
@login_required
def list_bonus():
    cid = _cid()
    fy = request.args.get('fy', type=int, default=date.today().year if date.today().month >= 4 else date.today().year - 1)
    records = (BonusRecord.query.join(Employee)
               .filter(Employee.company_id == cid, BonusRecord.financial_year == fy)
               .order_by(Employee.emp_code).all())
    years = list(range(2020, date.today().year + 1))
    return render_template('bonus/list.html', records=records, fy=fy, years=years)


@bonus_bp.route('/process', methods=['GET', 'POST'])
@login_required
def process_bonus():
    cid = _cid()
    today = date.today()
    current_fy = today.year if today.month >= 4 else today.year - 1
    years = list(range(2020, today.year + 1))

    if request.method == 'POST':
        fy = int(request.form.get('financial_year', current_fy))
        rate = float(request.form.get('bonus_rate', 8.33))
        emp_ids = request.form.getlist('emp_ids')

        employees = Employee.query.filter_by(company_id=cid).filter(
            Employee.id.in_([int(i) for i in emp_ids])
        ).all() if emp_ids else Employee.query.filter_by(company_id=cid).all()

        created = updated = 0
        for emp in employees:
            months = _eligible_months(emp, fy)
            if months == 0:
                continue
            basic_da = _annual_basic_da(emp, fy)
            # Statutory bonus: 8.33% of basic+DA subject to ₹7,000/month ceiling (₹84,000/year)
            ceiling = 7000 * months
            base = min(basic_da, ceiling)
            amount = round(base * rate / 100, 2)

            existing = BonusRecord.query.filter_by(employee_id=emp.id, financial_year=fy).first()
            if existing:
                existing.bonus_rate = rate
                existing.eligible_months = months
                existing.basic_da_annual = basic_da
                existing.bonus_amount = amount
                existing.status = 'calculated'
                updated += 1
            else:
                rec = BonusRecord(
                    employee_id=emp.id, company_id=cid,
                    financial_year=fy, bonus_rate=rate,
                    eligible_months=months, basic_da_annual=basic_da,
                    bonus_amount=amount, status='calculated',
                    processed_by=current_user.id,
                )
                db.session.add(rec)
                created += 1
        db.session.commit()
        flash(f'Bonus calculated: {created} new, {updated} updated for FY {fy}-{fy+1}.', 'success')
        return redirect(url_for('bonus.list_bonus', fy=fy))

    employees = Employee.query.filter_by(company_id=cid, is_active=True).order_by(Employee.emp_code).all()
    return render_template('bonus/process.html', employees=employees,
                           current_fy=current_fy, years=years)


@bonus_bp.route('/<int:rec_id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(rec_id):
    rec = BonusRecord.query.get_or_404(rec_id)
    rec.status = 'paid'
    rec.paid_date = date.today()
    db.session.commit()
    flash('Bonus marked as paid.', 'success')
    return redirect(url_for('bonus.list_bonus', fy=rec.financial_year))


@bonus_bp.route('/<int:rec_id>/discard', methods=['POST'])
@login_required
def discard(rec_id):
    rec = BonusRecord.query.get_or_404(rec_id)
    rec.status = 'discarded'
    db.session.commit()
    flash('Bonus discarded.', 'warning')
    return redirect(url_for('bonus.list_bonus', fy=rec.financial_year))
