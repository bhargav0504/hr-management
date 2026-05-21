from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, send_file, current_app)
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
from app.models.advance import Advance, AdvanceRepayment
from app.utils.payroll_calculator import calculate_payroll
from datetime import date, datetime
import calendar
import io

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')


@payroll_bp.route('/')
@login_required
def index():
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query
        .join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code)
        .all()
    )
    employees_with_payroll = {r.employee_id for r in records}
    pending_employees = (
        Employee.query
        .filter(
            Employee.is_active == True,
            ~Employee.id.in_(employees_with_payroll)
        )
        .order_by(Employee.emp_code)
        .all()
    )
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(2020, today.year + 2))
    totals = _compute_totals(records)
    return render_template('payroll/index.html',
                           records=records, pending_employees=pending_employees,
                           month=month, year=year, months=months, years=years, totals=totals)


@payroll_bp.route('/run', methods=['GET', 'POST'])
@login_required
def run_payroll():
    """Run payroll for all pending employees in a given month/year."""
    today = date.today()
    if request.method == 'POST':
        month = int(request.form.get('month', today.month))
        year = int(request.form.get('year', today.year))
        total_days = int(request.form.get('total_working_days', 26))

        employees = Employee.query.filter_by(is_active=True).all()
        created = 0
        skipped = 0
        for emp in employees:
            existing = SalaryRecord.query.filter_by(
                employee_id=emp.id, month=month, year=year
            ).first()
            if existing:
                skipped += 1
                continue

            # Present days from form (default = total_days)
            present_key = f'present_{emp.id}'
            present_days = float(request.form.get(present_key, total_days))

            # Advance deduction
            advance_deduction = _get_advance_deduction(emp, month, year)

            # YTD TDS
            ytd_tds = _get_ytd_tds(emp, month, year)

            data = calculate_payroll(
                employee=emp,
                month=month,
                year=year,
                present_days=present_days,
                total_working_days=total_days,
                advance_deduction=advance_deduction,
                ytd_tds=ytd_tds,
                config=current_app.config,
            )
            record = SalaryRecord(employee_id=emp.id, **data)
            record.status = 'processed'
            record.processed_at = datetime.utcnow()
            record.processed_by = current_user.id
            db.session.add(record)
            created += 1

        db.session.commit()
        flash(f'Payroll processed: {created} records created, {skipped} already existed.', 'success')
        return redirect(url_for('payroll.index', month=month, year=year))

    # GET — show form
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    total_days = int(request.args.get('total_days', 26))
    employees = Employee.query.filter_by(is_active=True).order_by(Employee.emp_code).all()
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(2020, today.year + 2))
    return render_template('payroll/run.html',
                           employees=employees, month=month, year=year,
                           months=months, years=years, total_days=total_days)


@payroll_bp.route('/record/<int:record_id>')
@login_required
def record_detail(record_id):
    record = SalaryRecord.query.get_or_404(record_id)
    return render_template('payroll/record_detail.html', record=record)


@payroll_bp.route('/record/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    record = SalaryRecord.query.get_or_404(record_id)
    if request.method == 'POST':
        # Manual override fields
        for field in ['present_days', 'tds', 'advance_deduction', 'other_deductions']:
            val = request.form.get(field, 0)
            setattr(record, field, float(val))
        record.other_deductions_remarks = request.form.get('other_deductions_remarks', '')

        # Recalculate using the calculator
        emp = record.employee
        data = calculate_payroll(
            employee=emp,
            month=record.month,
            year=record.year,
            present_days=float(record.present_days),
            total_working_days=record.total_working_days,
            advance_deduction=float(record.advance_deduction),
            ytd_tds=_get_ytd_tds(emp, record.month, record.year, exclude_id=record.id),
            config=current_app.config,
        )
        for k, v in data.items():
            setattr(record, k, v)
        record.tds = float(request.form.get('tds', record.tds))
        record.status = 'processed'
        record.processed_at = datetime.utcnow()
        record.processed_by = current_user.id
        db.session.commit()
        flash('Record updated.', 'success')
        return redirect(url_for('payroll.record_detail', record_id=record.id))
    return render_template('payroll/edit_record.html', record=record)


@payroll_bp.route('/record/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_record(record_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('payroll.index'))
    record = SalaryRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash('Payroll record deleted.', 'success')
    return redirect(url_for('payroll.index'))


@payroll_bp.route('/record/<int:record_id>/payslip')
@login_required
def download_payslip(record_id):
    from app.utils.pdf_generator import generate_payslip_pdf
    record = SalaryRecord.query.get_or_404(record_id)
    pdf_bytes = generate_payslip_pdf(record, current_app.config)
    buf = io.BytesIO(pdf_bytes)
    buf.seek(0)
    filename = f'payslip_{record.employee.emp_code}_{record.month:02d}_{record.year}.pdf'
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


@payroll_bp.route('/sheet')
@login_required
def salary_sheet():
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query
        .join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code)
        .all()
    )
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(2020, today.year + 2))
    totals = _compute_totals(records)
    return render_template('payroll/salary_sheet.html',
                           records=records, month=month, year=year,
                           months=months, years=years, totals=totals)


@payroll_bp.route('/export/excel')
@login_required
def export_excel():
    from app.utils.excel_exporter import export_salary_sheet
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query
        .join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code)
        .all()
    )
    wb_bytes = export_salary_sheet(records, month, year, current_app.config)
    buf = io.BytesIO(wb_bytes)
    buf.seek(0)
    filename = f'salary_sheet_{month:02d}_{year}.xlsx'
    return send_file(buf,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)


@payroll_bp.route('/export/pf-challan')
@login_required
def export_pf_challan():
    from app.utils.excel_exporter import export_pf_challan
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query.join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code).all()
    )
    wb_bytes = export_pf_challan(records, month, year, current_app.config)
    buf = io.BytesIO(wb_bytes)
    buf.seek(0)
    filename = f'pf_challan_{month:02d}_{year}.xlsx'
    return send_file(buf,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)


@payroll_bp.route('/export/esic-challan')
@login_required
def export_esic_challan():
    from app.utils.excel_exporter import export_esic_challan
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query.join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code).all()
    )
    wb_bytes = export_esic_challan(records, month, year, current_app.config)
    buf = io.BytesIO(wb_bytes)
    buf.seek(0)
    filename = f'esic_challan_{month:02d}_{year}.xlsx'
    return send_file(buf,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)


@payroll_bp.route('/export/pt-challan')
@login_required
def export_pt_challan():
    from app.utils.excel_exporter import export_pt_challan
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query.join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code).all()
    )
    wb_bytes = export_pt_challan(records, month, year, current_app.config)
    buf = io.BytesIO(wb_bytes)
    buf.seek(0)
    filename = f'pt_challan_{month:02d}_{year}.xlsx'
    return send_file(buf,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_advance_deduction(emp, month, year):
    active_advances = Advance.query.filter_by(employee_id=emp.id, status='active').all()
    total = 0
    for adv in active_advances:
        installment = min(float(adv.monthly_installment), float(adv.balance))
        if installment > 0:
            total += installment
    return total


def _get_ytd_tds(emp, month, year, exclude_id=None):
    fy_start = 4
    if month >= fy_start:
        fy_year = year
    else:
        fy_year = year - 1

    q = SalaryRecord.query.filter(
        SalaryRecord.employee_id == emp.id,
        db.or_(
            db.and_(SalaryRecord.year == fy_year, SalaryRecord.month >= fy_start),
            db.and_(SalaryRecord.year == fy_year + 1, SalaryRecord.month < fy_start),
        )
    )
    if exclude_id:
        q = q.filter(SalaryRecord.id != exclude_id)
    records = q.all()
    return sum(float(r.tds) for r in records)


def _compute_totals(records):
    fields = [
        'gross_earned', 'basic', 'pf_employee', 'pf_employer_total',
        'esic_employee', 'esic_employer', 'pt', 'lwf_employee', 'lwf_employer',
        'tds', 'advance_deduction', 'total_deductions', 'net_salary',
        'gratuity', 'bonus', 'ctc',
    ]
    return {f: sum(float(getattr(r, f) or 0) for r in records) for f in fields}
