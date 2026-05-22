from app import db
from datetime import datetime


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    short_name = db.Column(db.String(50))
    address = db.Column(db.Text)
    pan = db.Column(db.String(10))
    tan = db.Column(db.String(10))
    gst = db.Column(db.String(15))
    pf_no = db.Column(db.String(50))
    esic_no = db.Column(db.String(20))
    pt_no = db.Column(db.String(20))
    lwf_applicable = db.Column(db.Boolean, default=True)
    logo_filename = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Payroll settings (overrides config defaults)
    esic_ceiling = db.Column(db.Numeric(10, 2), default=21000)
    pf_wage_ceiling = db.Column(db.Numeric(10, 2), default=15000)
    pt_threshold = db.Column(db.Numeric(10, 2), default=12000)
    pt_amount = db.Column(db.Numeric(10, 2), default=200)

    employees = db.relationship('Employee', back_populates='company', lazy='dynamic')
    departments = db.relationship('Department', back_populates='company', cascade='all,delete-orphan')
    designations = db.relationship('Designation', back_populates='company', cascade='all,delete-orphan')
    categories = db.relationship('Category', back_populates='company', cascade='all,delete-orphan')
    locations = db.relationship('Location', back_populates='company', cascade='all,delete-orphan')
    leave_types = db.relationship('LeaveType', back_populates='company', cascade='all,delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'
