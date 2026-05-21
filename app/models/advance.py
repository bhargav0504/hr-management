from app import db
from datetime import datetime

class Advance(db.Model):
    __tablename__ = 'advances'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    disbursed_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(300), nullable=True)

    # Repayment
    monthly_installment = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_repaid = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), default='active')  # active, closed

    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', back_populates='advances')
    approver = db.relationship('User', foreign_keys=[approved_by])
    repayments = db.relationship('AdvanceRepayment', back_populates='advance', lazy='dynamic')

    def __repr__(self):
        return f'<Advance emp={self.employee_id} amt={self.amount}>'


class AdvanceRepayment(db.Model):
    __tablename__ = 'advance_repayments'

    id = db.Column(db.Integer, primary_key=True)
    advance_id = db.Column(db.Integer, db.ForeignKey('advances.id'), nullable=False)
    salary_record_id = db.Column(db.Integer, db.ForeignKey('salary_records.id'), nullable=True)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    advance = db.relationship('Advance', back_populates='repayments')
