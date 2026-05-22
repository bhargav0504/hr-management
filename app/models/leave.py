from app import db
from datetime import datetime


class LeaveType(db.Model):
    __tablename__ = 'leave_types'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    code = db.Column(db.String(10), nullable=False)   # PL, SL, CL, ML, EL, WO
    name = db.Column(db.String(100), nullable=False)
    days_per_year = db.Column(db.Integer, default=0)
    carry_forward_max = db.Column(db.Integer, default=0)
    is_paid = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)

    company = db.relationship('Company', back_populates='leave_types')
    balances = db.relationship('LeaveBalance', back_populates='leave_type', cascade='all,delete-orphan')
    applications = db.relationship('LeaveApplication', back_populates='leave_type', cascade='all,delete-orphan')

    def __repr__(self):
        return f'<LeaveType {self.code}>'


class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    allocated = db.Column(db.Numeric(5, 1), default=0)
    used = db.Column(db.Numeric(5, 1), default=0)
    balance = db.Column(db.Numeric(5, 1), default=0)

    employee = db.relationship('Employee', back_populates='leave_balances')
    leave_type = db.relationship('LeaveType', back_populates='balances')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'leave_type_id', 'year', name='uq_leave_bal'),
    )


class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Numeric(5, 1), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    remarks = db.Column(db.Text)

    employee = db.relationship('Employee', back_populates='leave_applications')
    leave_type = db.relationship('LeaveType', back_populates='applications')
    approver = db.relationship('User', foreign_keys=[approved_by])

    def __repr__(self):
        return f'<LeaveApplication emp={self.employee_id} {self.from_date}>'
