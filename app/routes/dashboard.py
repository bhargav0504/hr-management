from flask import Blueprint, render_template
from flask_login import login_required
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
from app.models.advance import Advance
from datetime import date

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    today = date.today()
    stats = {
        'total_employees': Employee.query.filter_by(is_active=True).count(),
        'pending_payroll': SalaryRecord.query.filter_by(
            month=today.month, year=today.year, status='draft'
        ).count(),
        'active_advances': Advance.query.filter_by(status='active').count(),
        'departments': Employee.query.with_entities(Employee.department).distinct().count(),
    }
    recent_payroll = (
        SalaryRecord.query
        .filter_by(month=today.month, year=today.year)
        .order_by(SalaryRecord.created_at.desc())
        .limit(10).all()
    )
    return render_template('dashboard/index.html', stats=stats, recent_payroll=recent_payroll, today=today)
