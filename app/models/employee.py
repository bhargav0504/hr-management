from app import db
from datetime import datetime, date


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    emp_code = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), default='Male')
    marital_status = db.Column(db.String(15), default='Single')
    father_husband_name = db.Column(db.String(200), nullable=True)
    photo_filename = db.Column(db.String(200), nullable=True)

    date_of_birth = db.Column(db.Date, nullable=True)
    date_of_joining = db.Column(db.Date, nullable=False)
    date_of_leaving = db.Column(db.Date, nullable=True)
    reason_for_leaving = db.Column(db.String(50), nullable=True)   # resignation/termination/retirement/other
    leaving_remarks = db.Column(db.Text, nullable=True)

    # Master-linked fields (stored as string for flexibility + bulk import compat)
    department = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True, default='Head Office')
    employment_type = db.Column(db.String(20), default='permanent')

    # Contact
    mobile = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)

    # Statutory IDs
    pan_number = db.Column(db.String(10), nullable=True)
    aadhaar_number = db.Column(db.String(12), nullable=True)
    uan_number = db.Column(db.String(12), nullable=True)
    esic_ip_number = db.Column(db.String(17), nullable=True)

    # Bank details
    bank_account = db.Column(db.String(20), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    ifsc_code = db.Column(db.String(11), nullable=True)

    # Salary structure
    gross_ctc = db.Column(db.Numeric(10, 2), default=0)
    basic_salary = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    hra = db.Column(db.Numeric(10, 2), default=0)
    da = db.Column(db.Numeric(10, 2), default=0)
    special_allowance = db.Column(db.Numeric(10, 2), default=0)
    other_allowance = db.Column(db.Numeric(10, 2), default=0)
    petrol_allowance = db.Column(db.Numeric(10, 2), default=0)
    conveyance = db.Column(db.Numeric(10, 2), default=0)
    medical_allowance = db.Column(db.Numeric(10, 2), default=0)

    # Statutory flags
    pf_applicable = db.Column(db.Boolean, default=True)
    pf_on_ceiling = db.Column(db.Boolean, default=True)
    pension_eligible = db.Column(db.Boolean, default=True)
    esic_applicable = db.Column(db.Boolean, default=True)
    pt_applicable = db.Column(db.Boolean, default=True)
    tds_regime = db.Column(db.String(10), default='new')

    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique per company
    __table_args__ = (
        db.UniqueConstraint('company_id', 'emp_code', name='uq_company_emp_code'),
    )

    # Relationships
    company = db.relationship('Company', back_populates='employees')
    salary_records = db.relationship('SalaryRecord', back_populates='employee', lazy='dynamic')
    advances = db.relationship('Advance', back_populates='employee', lazy='dynamic')
    family_members   = db.relationship('EmployeeFamily',        back_populates='employee', cascade='all,delete-orphan')
    education_details= db.relationship('EmployeeEducation',     back_populates='employee', cascade='all,delete-orphan')
    prev_employments = db.relationship('EmployeePrevEmployment',back_populates='employee', cascade='all,delete-orphan')
    leave_balances = db.relationship('LeaveBalance', back_populates='employee', cascade='all,delete-orphan')
    leave_applications = db.relationship('LeaveApplication', back_populates='employee', cascade='all,delete-orphan')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def gross_salary(self):
        components = float(
            self.basic_salary + self.hra + self.da +
            self.special_allowance + self.other_allowance +
            self.petrol_allowance + self.conveyance + self.medical_allowance
        )
        ctc = float(self.gross_ctc or 0)
        return ctc if ctc > 0 else components

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return (today - self.date_of_birth).days // 365

    def __repr__(self):
        return f'<Employee {self.emp_code} - {self.full_name}>'
