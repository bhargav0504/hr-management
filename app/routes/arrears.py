from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.arrears import ArrearRecord
from datetime import date
import calendar

arrears_bp = Blueprint('arrears', __name__, url_prefix='/arrears')


def _cid():
    return session.get('company_id')


ARREAR_HEADS = [
    ('salary', 'Salary Arrear'),
    ('da', 'DA Arrear'),
    ('hra', 'HRA Arrear'),
    ('leave_encashment', 'Leave Encashment'),
    ('advance', 'Advance'),
    ('income_tax', 'Income Tax'),
    ('other', 'Other'),
]


@arrears_bp.route('/')
@arrears_bp.route('/list')
@login_required
def list_arrears():
    cid = _cid()
    status = request.args.get('status', 'pending')
    q = request.args.get('q', '').strip()
    query = ArrearRecord.query.join(Employee).filter(Employee.company_id == cid)
    if status in ('pending', 'paid', 'cancelled'):
        query = query.filter(ArrearRecord.status == status)
    if q:
        query = query.filter(
            db.or_(Employee.first_name.ilike(f'%{q}%'),
                   Employee.last_name.ilike(f'%{q}%'),
                   Employee.emp_code.ilike(f'%{q}%'))
        )
    records = query.order_by(ArrearRecord.created_at.desc()).all()
    return render_template('arrears/list.html', records=records, status=status, q=q)


@arrears_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_arrear():
    cid = _cid()
    today = date.today()
    employees = Employee.query.filter_by(company_id=cid, is_active=True).order_by(Employee.emp_code).all()
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(2020, today.year + 2))

    if request.method == 'POST':
        emp_ids = request.form.getlist('employee_ids')
        if not emp_ids:
            flash('Select at least one employee.', 'danger')
            return redirect(url_for('arrears.add_arrear'))

        count = 0
        for eid in emp_ids:
            emp = Employee.query.filter_by(id=int(eid), company_id=cid).first()
            if not emp:
                continue
            rec = ArrearRecord(
                employee_id=int(eid),
                company_id=cid,
                arrear_type=request.form.get('arrear_type', 'pay'),
                arrear_head=request.form.get('arrear_head', 'salary'),
                description=request.form.get('description', '').strip(),
                from_month=int(request.form.get('from_month', today.month)),
                from_year=int(request.form.get('from_year', today.year)),
                to_month=int(request.form.get('to_month', today.month)),
                to_year=int(request.form.get('to_year', today.year)),
                amount=float(request.form.get('amount', 0) or 0),
                is_taxable=request.form.get('is_taxable') == 'on',
                remarks=request.form.get('remarks', '').strip(),
                created_by=current_user.id,
            )
            db.session.add(rec)
            count += 1
        db.session.commit()
        flash(f'{count} arrear record(s) added.', 'success')
        return redirect(url_for('arrears.list_arrears'))

    return render_template('arrears/form.html', employees=employees,
                           months=months, years=years, today=today,
                           arrear_heads=ARREAR_HEADS)


@arrears_bp.route('/<int:arr_id>/pay', methods=['POST'])
@login_required
def mark_paid(arr_id):
    rec = ArrearRecord.query.get_or_404(arr_id)
    today = date.today()
    rec.status = 'paid'
    rec.paid_month = today.month
    rec.paid_year = today.year
    db.session.commit()
    flash('Arrear marked as paid.', 'success')
    return redirect(url_for('arrears.list_arrears'))


@arrears_bp.route('/<int:arr_id>/cancel', methods=['POST'])
@login_required
def cancel_arrear(arr_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('arrears.list_arrears'))
    rec = ArrearRecord.query.get_or_404(arr_id)
    rec.status = 'cancelled'
    db.session.commit()
    flash('Arrear cancelled.', 'warning')
    return redirect(url_for('arrears.list_arrears'))


@arrears_bp.route('/<int:arr_id>/delete', methods=['POST'])
@login_required
def delete_arrear(arr_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('arrears.list_arrears'))
    rec = ArrearRecord.query.get_or_404(arr_id)
    db.session.delete(rec)
    db.session.commit()
    flash('Arrear deleted.', 'success')
    return redirect(url_for('arrears.list_arrears'))
