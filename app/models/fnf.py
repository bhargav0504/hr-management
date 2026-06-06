from app import db
from datetime import datetime


class FnFRecord(db.Model):
    __tablename__ = 'fnf_records'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    # Exit details
    resignation_date = db.Column(db.Date, nullable=True)
    last_working_day = db.Column(db.Date, nullable=False)
    settlement_date = db.Column(db.Date, nullable=True)
    reason = db.Column(db.String(50))           # resignation/termination/retirement/absconding/other
    notice_period_days = db.Column(db.Integer, default=0)

    # Earnings in F&F
    salary_days = db.Column(db.Integer, default=0)          # days worked in final month
    salary_for_days = db.Column(db.Numeric(10, 2), default=0)
    leave_encashment_days = db.Column(db.Numeric(5, 1), default=0)
    leave_encashment = db.Column(db.Numeric(10, 2), default=0)
    gratuity = db.Column(db.Numeric(10, 2), default=0)
    bonus = db.Column(db.Numeric(10, 2), default=0)
    other_earnings = db.Column(db.Numeric(10, 2), default=0)
    other_earnings_remarks = db.Column(db.String(200))

    # Deductions in F&F
    notice_period_recovery = db.Column(db.Numeric(10, 2), default=0)
    advance_recovery = db.Column(db.Numeric(10, 2), default=0)
    other_deductions = db.Column(db.Numeric(10, 2), default=0)
    other_deductions_remarks = db.Column(db.String(200))

    # Totals
    total_earnings = db.Column(db.Numeric(10, 2), default=0)
    total_deductions = db.Column(db.Numeric(10, 2), default=0)
    net_settlement = db.Column(db.Numeric(10, 2), default=0)

    status = db.Column(db.String(20), default='draft')   # draft / settled / cancelled
    remarks = db.Column(db.Text)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref='fnf_records')
