from flask import Blueprint, render_template, request, send_file, current_app
from flask_login import login_required
from app import db
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
import calendar
from datetime import date
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    today = date.today()
    years = list(range(2020, today.year + 2))
    return render_template('reports/index.html', today=today, years=years)


@reports_bp.route('/tds-summary')
@login_required
def tds_summary():
    today = date.today()
    fy_year = int(request.args.get('fy_year', today.year if today.month >= 4 else today.year - 1))

    records = (
        SalaryRecord.query.join(Employee)
        .filter(
            db.or_(
                db.and_(SalaryRecord.year == fy_year, SalaryRecord.month >= 4),
                db.and_(SalaryRecord.year == fy_year + 1, SalaryRecord.month < 4),
            )
        )
        .order_by(Employee.emp_code, SalaryRecord.year, SalaryRecord.month)
        .all()
    )

    # Group by employee
    emp_data = {}
    for r in records:
        eid = r.employee_id
        if eid not in emp_data:
            emp_data[eid] = {
                'employee': r.employee,
                'months': [],
                'total_gross': 0,
                'total_tds': 0,
            }
        emp_data[eid]['months'].append(r)
        emp_data[eid]['total_gross'] += float(r.gross_earned or 0)
        emp_data[eid]['total_tds'] += float(r.tds or 0)

    years = list(range(2020, today.year + 2))
    return render_template('reports/tds_summary.html',
                           emp_data=emp_data, fy_year=fy_year, years=years)


@reports_bp.route('/tds-summary/export')
@login_required
def export_tds_summary():
    from app.utils.excel_exporter import export_tds_summary_excel
    today = date.today()
    fy_year = int(request.args.get('fy_year', today.year if today.month >= 4 else today.year - 1))
    records = (
        SalaryRecord.query.join(Employee)
        .filter(
            db.or_(
                db.and_(SalaryRecord.year == fy_year, SalaryRecord.month >= 4),
                db.and_(SalaryRecord.year == fy_year + 1, SalaryRecord.month < 4),
            )
        )
        .order_by(Employee.emp_code, SalaryRecord.year, SalaryRecord.month)
        .all()
    )
    wb_bytes = export_tds_summary_excel(records, fy_year, current_app.config)
    buf = io.BytesIO(wb_bytes)
    buf.seek(0)
    return send_file(buf,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name=f'tds_summary_FY{fy_year}-{fy_year+1}.xlsx')


@reports_bp.route('/pt-summary')
@login_required
def pt_summary():
    today = date.today()
    month = int(request.args.get('month', today.month))
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query.join(Employee)
        .filter(SalaryRecord.month == month, SalaryRecord.year == year)
        .order_by(Employee.emp_code).all()
    )
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(2020, today.year + 2))
    pt_records = [r for r in records if float(r.pt or 0) > 0]
    total_pt = sum(float(r.pt or 0) for r in pt_records)
    return render_template('reports/pt_summary.html',
                           records=pt_records, all_count=len(records),
                           month=month, year=year, months=months, years=years, total_pt=total_pt)


@reports_bp.route('/lwf-summary')
@login_required
def lwf_summary():
    today = date.today()
    year = int(request.args.get('year', today.year))
    records = (
        SalaryRecord.query.join(Employee)
        .filter(
            SalaryRecord.year == year,
            SalaryRecord.month.in_([6, 12]),
        )
        .order_by(Employee.emp_code, SalaryRecord.month)
        .all()
    )
    years = list(range(2020, today.year + 2))
    totals = {
        'lwf_employee': sum(float(r.lwf_employee or 0) for r in records),
        'lwf_employer': sum(float(r.lwf_employer or 0) for r in records),
    }
    return render_template('reports/lwf_summary.html',
                           records=records, year=year, years=years, totals=totals)
