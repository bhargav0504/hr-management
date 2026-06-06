from app import db
from datetime import datetime


class ArrearRecord(db.Model):
    __tablename__ = 'arrear_records'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    arrear_type = db.Column(db.String(10), default='pay')     # pay / collect
    arrear_head = db.Column(db.String(50))                    # salary / da / hra / leave_encashment / advance / income_tax / other
    description = db.Column(db.String(200))

    # Period the arrear relates to
    from_month = db.Column(db.Integer)
    from_year = db.Column(db.Integer)
    to_month = db.Column(db.Integer)
    to_year = db.Column(db.Integer)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    is_taxable = db.Column(db.Boolean, default=True)

    # Payment tracking
    status = db.Column(db.String(20), default='pending')      # pending / paid / cancelled
    paid_month = db.Column(db.Integer, nullable=True)
    paid_year = db.Column(db.Integer, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.String(300))

    employee = db.relationship('Employee', backref='arrear_records')
