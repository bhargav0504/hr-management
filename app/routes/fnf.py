from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.fnf import FnFRecord
from app.models.advance import Advance
from datetime import date, datetime
import calendar

fnf_bp = Blueprint('fnf', __name__, url_prefix='/fnf')


def _cid():
    return session.get('company_id')


def _compute_fnf(emp, last_working_day, salary_days, leave_days, notice_recovery_days=0):
    """Auto-calculate F&F components from employee data."""
    gross = float(emp.gross_salary or 0)
    basic = float(emp.basic_salary or 0)
    daily_rate = gross / 26

    salary_for_days = round(daily_rate * salary_days, 2)
    leave_encashment = round((basic / 26) * float(leave_days), 2)

    # Gratuity: 15/26 × last basic × completed years (eligible if ≥ 5 years)
    years = 0
    if emp.date_of_joining:
        delta = last_working_day - emp.date_of_joining
        years = delta.days // 365
    gratuity = round((basic / 26) * 15 * years, 2) if years >= 5 else 0

    notice_recovery = round(daily_rate * notice_recovery_days, 2)

    # Outstanding advances
    advance_recovery = sum(
        float(a.balance) for a in Advance.query.filter_by(employee_id=emp.id, status='active').all()
    )

    return {
        'salary_for_days': salary_for_days,
        'leave_encashment': leave_encashment,
        'gratuity': gratuity,
        'notice_period_recovery': notice_recovery,
        'advance_recovery': round(advance_recovery, 2),
    }


@fnf_bp.route('/')
@login_required
def list_fnf():
    cid = _cid()
    records = (FnFRecord.query.join(Employee)
               .filter(Employee.company_id == cid)
               .order_by(FnFRecord.created_at.desc()).all())
    return render_template('fnf/list.html', records=records)


@fnf_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_fnf():
    cid = _cid()
    employees = Employee.query.filter_by(company_id=cid, is_active=True).order_by(Employee.emp_code).all()

    if request.method == 'POST':
        emp_id = int(request.form.get('employee_id', 0))
        emp = Employee.query.filter_by(id=emp_id, company_id=cid).first()
        if not emp:
            flash('Invalid employee.', 'danger')
            return redirect(url_for('fnf.create_fnf'))

        def _d(field, default=0):
            v = request.form.get(field, '').strip()
            return float(v) if v else default

        def _date(field):
            v = request.form.get(field, '').strip()
            return datetime.strptime(v, '%Y-%m-%d').date() if v else None

        last_day = _date('last_working_day') or date.today()
        total_e = _d('salary_for_days') + _d('leave_encashment') + _d('gratuity') + _d('bonus') + _d('other_earnings')
        total_d = _d('notice_period_recovery') + _d('advance_recovery') + _d('other_deductions')

        record = FnFRecord(
            employee_id=emp_id,
            company_id=cid,
            resignation_date=_date('resignation_date'),
            last_working_day=last_day,
            settlement_date=_date('settlement_date'),
            reason=request.form.get('reason', ''),
            notice_period_days=int(_d('notice_period_days')),
            salary_days=int(_d('salary_days')),
            salary_for_days=_d('salary_for_days'),
            leave_encashment_days=_d('leave_encashment_days'),
            leave_encashment=_d('leave_encashment'),
            gratuity=_d('gratuity'),
            bonus=_d('bonus'),
            other_earnings=_d('other_earnings'),
            other_earnings_remarks=request.form.get('other_earnings_remarks', ''),
            notice_period_recovery=_d('notice_period_recovery'),
            advance_recovery=_d('advance_recovery'),
            other_deductions=_d('other_deductions'),
            other_deductions_remarks=request.form.get('other_deductions_remarks', ''),
            total_earnings=round(total_e, 2),
            total_deductions=round(total_d, 2),
            net_settlement=round(total_e - total_d, 2),
            remarks=request.form.get('remarks', ''),
            status='draft',
            processed_by=current_user.id,
        )
        db.session.add(record)

        # Mark employee inactive
        emp.is_active = False
        emp.date_of_leaving = last_day
        emp.reason_for_leaving = request.form.get('reason', '')
        db.session.commit()

        flash(f'F&F record created for {emp.full_name}. Net settlement: ₹{record.net_settlement:,.2f}', 'success')
        return redirect(url_for('fnf.detail', fnf_id=record.id))

    # GET — pre-calculate if employee selected
    pre = {}
    emp_id = request.args.get('emp_id', type=int)
    selected_emp = None
    if emp_id:
        selected_emp = Employee.query.filter_by(id=emp_id, company_id=cid).first()
        if selected_emp:
            pre = _compute_fnf(selected_emp, date.today(), 13, 0)

    return render_template('fnf/form.html', employees=employees, pre=pre,
                           selected_emp=selected_emp, today=date.today())


@fnf_bp.route('/<int:fnf_id>')
@login_required
def detail(fnf_id):
    record = FnFRecord.query.get_or_404(fnf_id)
    return render_template('fnf/detail.html', r=record)


@fnf_bp.route('/<int:fnf_id>/settle', methods=['POST'])
@login_required
def settle(fnf_id):
    record = FnFRecord.query.get_or_404(fnf_id)
    record.status = 'settled'
    record.settlement_date = date.today()
    db.session.commit()
    flash('F&F marked as settled.', 'success')
    return redirect(url_for('fnf.detail', fnf_id=fnf_id))


@fnf_bp.route('/<int:fnf_id>/cancel', methods=['POST'])
@login_required
def cancel_fnf(fnf_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('fnf.list_fnf'))
    record = FnFRecord.query.get_or_404(fnf_id)
    record.status = 'cancelled'
    db.session.commit()
    flash('F&F cancelled.', 'warning')
    return redirect(url_for('fnf.list_fnf'))
