from app import db
from datetime import datetime


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    short_name = db.Column(db.String(50))
    company_type = db.Column(db.String(50))          # Pvt Ltd, LLP, Partnership, etc.
    formation_date = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    pin = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    pan = db.Column(db.String(10))
    tan = db.Column(db.String(10))
    gst = db.Column(db.String(15))
    pf_no = db.Column(db.String(50))
    esic_no = db.Column(db.String(20))
    pt_no = db.Column(db.String(20))
    lwf_no = db.Column(db.String(20))
    lwf_applicable = db.Column(db.Boolean, default=True)
    # Key people
    authorised_signatory = db.Column(db.String(200))
    manager_name = db.Column(db.String(200))
    logo_filename = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Payroll settings
    esic_ceiling = db.Column(db.Numeric(10, 2), default=21000)
    pf_wage_ceiling = db.Column(db.Numeric(10, 2), default=15000)
    pt_threshold = db.Column(db.Numeric(10, 2), default=12000)
    pt_amount = db.Column(db.Numeric(10, 2), default=200)

    # Salary Structure Template (% of gross CTC, applied when adding employees)
    ss_basic_pct = db.Column(db.Numeric(5, 2), default=50)        # Basic % of gross
    ss_hra_pct = db.Column(db.Numeric(5, 2), default=40)          # HRA % of basic
    ss_da_pct = db.Column(db.Numeric(5, 2), default=0)            # DA % of basic
    ss_special_pct = db.Column(db.Numeric(5, 2), default=0)       # Special Allow % of gross
    ss_other_pct = db.Column(db.Numeric(5, 2), default=0)         # Other Allow % of gross
    ss_conveyance_pct = db.Column(db.Numeric(5, 2), default=0)    # Conveyance % of gross
    ss_medical_pct = db.Column(db.Numeric(5, 2), default=0)       # Medical Allow % of gross
    ss_petrol_pct = db.Column(db.Numeric(5, 2), default=0)        # Petrol Allow % of gross

    employees = db.relationship('Employee', back_populates='company', lazy='dynamic')
    branches = db.relationship('Branch', back_populates='company', cascade='all,delete-orphan')
    departments = db.relationship('Department', back_populates='company', cascade='all,delete-orphan')
    designations = db.relationship('Designation', back_populates='company', cascade='all,delete-orphan')
    categories = db.relationship('Category', back_populates='company', cascade='all,delete-orphan')
    locations = db.relationship('Location', back_populates='company', cascade='all,delete-orphan')
    leave_types = db.relationship('LeaveType', back_populates='company', cascade='all,delete-orphan')
    salary_components = db.relationship('SalaryComponent', back_populates='company', cascade='all,delete-orphan')

    def __repr__(self):
        return f'<Company {self.name}>'
