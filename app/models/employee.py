from app import db
from datetime import datetime

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    emp_code = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=True, default='Male')  # Male / Female
    marital_status = db.Column(db.String(15), nullable=True, default='Single')  # Married / Single
    father_husband_name = db.Column(db.String(200), nullable=True)

    date_of_birth = db.Column(db.Date, nullable=True)
    date_of_joining = db.Column(db.Date, nullable=False)
    date_of_leaving = db.Column(db.Date, nullable=True)

    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=True, default='Head Office')
    designation = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)      # Worker / Staff / Management
    employment_type = db.Column(db.String(20), default='permanent')  # permanent, contract

    # Contact
    mobile = db.Column(db.String(15), nullable=True)
    alt_mobile = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)

    # Statutory IDs
    pan_number = db.Column(db.String(10), nullable=True)
    aadhaar_number = db.Column(db.String(12), nullable=True)
    uan_number = db.Column(db.String(12), nullable=True)    # PF UAN
    esic_ip_number = db.Column(db.String(17), nullable=True)
    disp_no = db.Column(db.String(20), nullable=True)       # ESIC dispensary

    # Bank details
    bank_account = db.Column(db.String(20), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    ifsc_code = db.Column(db.String(11), nullable=True)

    # Salary structure (monthly CTC components)
    gross_ctc = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # Total Gross CTC
    basic_salary = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    hra = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    da = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    special_allowance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    other_allowance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    petrol_allowance = db.Column(db.Numeric(10, 2), nullable=False, default=0)   # excluded from PF base
    conveyance = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    medical_allowance = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # Statutory flags
    pf_applicable = db.Column(db.Boolean, default=True)
    pf_on_ceiling = db.Column(db.Boolean, default=True)   # True = cap PF at ₹15,000 basic; False = full contribution
    pension_eligible = db.Column(db.Boolean, default=True)
    esic_applicable = db.Column(db.Boolean, default=True)
    pt_applicable = db.Column(db.Boolean, default=True)   # Professional Tax
    tds_regime = db.Column(db.String(10), default='new')  # 'new' or 'old'

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    salary_records = db.relationship('SalaryRecord', back_populates='employee', lazy='dynamic')
    advances = db.relationship('Advance', back_populates='employee', lazy='dynamic')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def gross_salary(self):
        """Total of all CTC salary components (use gross_ctc if set)."""
        components = float(
            self.basic_salary + self.hra + self.da +
            self.special_allowance + self.other_allowance +
            self.petrol_allowance + self.conveyance + self.medical_allowance
        )
        # If gross_ctc is explicitly set and > 0, prefer it
        ctc = float(self.gross_ctc or 0)
        return ctc if ctc > 0 else components

    def __repr__(self):
        return f'<Employee {self.emp_code} - {self.full_name}>'
