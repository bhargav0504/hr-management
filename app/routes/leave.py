from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.employee import Employee
from app.models.leave import LeaveType, LeaveBalance, LeaveApplication

leave_bp = Blueprint('leave', __name__, url_prefix='/leave')


def _get_company_id():
    return session.get('company_id')


@leave_bp.route('/')
@login_required
def list_applications():
    cid = _get_company_id()
    status = request.args.get('status', '')
    q = LeaveApplication.query.join(Employee).filter(Employee.company_id == cid)
    if status:
        q = q.filter(LeaveApplication.status == status)
    applications = q.order_by(LeaveApplication.applied_at.desc()).all()
    return render_template('leave/list.html', applications=applications, status=status)


@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    cid = _get_company_id()
    employees = Employee.query.filter_by(company_id=cid, is_active=True).order_by(Employee.emp_code).all()
    leave_types = LeaveType.query.filter_by(company_id=cid, is_active=True).order_by(LeaveType.code).all()

    if request.method == 'POST':
        emp_id = int(request.form.get('employee_id'))
        lt_id = int(request.form.get('leave_type_id'))
        from_date = datetime.strptime(request.form.get('from_date'), '%Y-%m-%d').date()
        to_date = datetime.strptime(request.form.get('to_date'), '%Y-%m-%d').date()
        reason = request.form.get('reason', '')

        if to_date < from_date:
            flash('To date cannot be before From date.', 'danger')
            return render_template('leave/apply.html', employees=employees, leave_types=leave_types)

        days = (to_date - from_date).days + 1
        app_rec = LeaveApplication(
            employee_id=emp_id, leave_type_id=lt_id,
            from_date=from_date, to_date=to_date,
            days=days, reason=reason, status='pending'
        )
        db.session.add(app_rec)
        db.session.commit()
        flash('Leave application submitted.', 'success')
        return redirect(url_for('leave.list_applications'))

    return render_template('leave/apply.html', employees=employees, leave_types=leave_types)


@leave_bp.route('/<int:app_id>/approve', methods=['POST'])
@login_required
def approve(app_id):
    app_rec = LeaveApplication.query.get_or_404(app_id)
    app_rec.status = 'approved'
    app_rec.approved_by = current_user.id
    app_rec.approved_at = datetime.utcnow()
    app_rec.remarks = request.form.get('remarks', '')
    db.session.commit()
    flash('Leave approved.', 'success')
    return redirect(url_for('leave.list_applications'))


@leave_bp.route('/<int:app_id>/reject', methods=['POST'])
@login_required
def reject(app_id):
    app_rec = LeaveApplication.query.get_or_404(app_id)
    app_rec.status = 'rejected'
    app_rec.approved_by = current_user.id
    app_rec.approved_at = datetime.utcnow()
    app_rec.remarks = request.form.get('remarks', '')
    db.session.commit()
    flash('Leave rejected.', 'warning')
    return redirect(url_for('leave.list_applications'))


@leave_bp.route('/balances')
@login_required
def balances():
    cid = _get_company_id()
    year = int(request.args.get('year', datetime.now().year))
    employees = Employee.query.filter_by(company_id=cid, is_active=True).order_by(Employee.emp_code).all()
    leave_types = LeaveType.query.filter_by(company_id=cid, is_active=True).all()
    return render_template('leave/balances.html', employees=employees,
                           leave_types=leave_types, year=year)


@leave_bp.route('/balances/allocate', methods=['POST'])
@login_required
def allocate():
    emp_id = int(request.form.get('employee_id'))
    lt_id = int(request.form.get('leave_type_id'))
    year = int(request.form.get('year'))
    days = float(request.form.get('days', 0))

    bal = LeaveBalance.query.filter_by(employee_id=emp_id, leave_type_id=lt_id, year=year).first()
    if bal:
        bal.allocated = days
        bal.balance = max(0, days - float(bal.used))
    else:
        db.session.add(LeaveBalance(employee_id=emp_id, leave_type_id=lt_id,
                                    year=year, allocated=days, used=0, balance=days))
    db.session.commit()
    flash('Leave balance updated.', 'success')
    return redirect(url_for('leave.balances', year=year))
