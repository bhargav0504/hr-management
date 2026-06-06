from app import db
from datetime import datetime


class BonusRecord(db.Model):
    __tablename__ = 'bonus_records'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    financial_year = db.Column(db.Integer, nullable=False)   # e.g. 2024 for FY 2024-25
    bonus_rate = db.Column(db.Numeric(5, 2), default=8.33)   # %
    eligible_months = db.Column(db.Integer, default=12)       # months of service in FY
    basic_da_annual = db.Column(db.Numeric(10, 2), default=0) # annual basic+DA used as base
    bonus_amount = db.Column(db.Numeric(10, 2), default=0)    # calculated bonus

    status = db.Column(db.String(20), default='calculated')   # calculated / paid / discarded
    paid_date = db.Column(db.Date, nullable=True)
    remarks = db.Column(db.String(200))
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', backref='bonus_records')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'financial_year', name='uq_bonus_emp_fy'),
    )
