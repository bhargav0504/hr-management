from flask import Blueprint, render_template, session
from flask_login import login_required
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
from app.models.advance import Advance
from app import db
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    company_id = session.get('company_id')
    stats = {
        'total_employees': Employee.query.filter_by(is_active=True, company_id=company_id).count(),
        'pending_payroll': (
            SalaryRecord.query.join(Employee)
            .filter(Employee.company_id == company_id,
                    SalaryRecord.month == today.month,
                    SalaryRecord.year == today.year,
                    SalaryRecord.status == 'draft')
            .count()
        ),
        'active_advances': (
            Advance.query.join(Employee)
            .filter(Employee.company_id == company_id, Advance.status == 'active')
            .count()
        ),
        'departments': (
            Employee.query
            .filter_by(is_active=True, company_id=company_id)
            .with_entities(Employee.department).distinct().count()
        ),
    }
    recent_payroll = (
        SalaryRecord.query.join(Employee)
        .filter(Employee.company_id == company_id,
                SalaryRecord.month == today.month,
                SalaryRecord.year == today.year)
        .order_by(SalaryRecord.created_at.desc())
        .limit(10).all()
    )
    return render_template('dashboard/index.html', stats=stats, recent_payroll=recent_payroll, today=today)
