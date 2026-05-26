from app import db
from datetime import datetime

class SalaryRecord(db.Model):
    __tablename__ = 'salary_records'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)   # 1-12
    year = db.Column(db.Integer, nullable=False)

    # Working days
    total_working_days = db.Column(db.Integer, nullable=False, default=26)
    present_days = db.Column(db.Numeric(5, 1), nullable=False, default=26)
    lop_days = db.Column(db.Numeric(5, 1), nullable=False, default=0)

    # Earnings — actual (prorated to present days)
    basic = db.Column(db.Numeric(10, 2), default=0)
    hra = db.Column(db.Numeric(10, 2), default=0)
    da = db.Column(db.Numeric(10, 2), default=0)
    special_allowance = db.Column(db.Numeric(10, 2), default=0)
    other_allowance = db.Column(db.Numeric(10, 2), default=0)
    petrol_allowance = db.Column(db.Numeric(10, 2), default=0)   # excluded from PF base
    conveyance = db.Column(db.Numeric(10, 2), default=0)
    medical_allowance = db.Column(db.Numeric(10, 2), default=0)
    gross_earned = db.Column(db.Numeric(10, 2), default=0)       # full earned gross
    pf_wage_base = db.Column(db.Numeric(10, 2), default=0)       # earned gross excl. petrol (PF base)

    # Employee deductions
    pf_employee = db.Column(db.Numeric(10, 2), default=0)        # 12% of pf_wage_base (capped ₹15,000)
    esic_employee = db.Column(db.Numeric(10, 2), default=0)      # 0.75% of gross
    pt = db.Column(db.Numeric(10, 2), default=0)                 # Professional Tax (Gujarat ₹200 if gross≥₹12,000)
    lwf_employee = db.Column(db.Numeric(10, 2), default=0)       # ₹6 in Jun/Dec
    tds = db.Column(db.Numeric(10, 2), default=0)
    advance_deduction = db.Column(db.Numeric(10, 2), default=0)
    other_deductions = db.Column(db.Numeric(10, 2), default=0)
    other_deductions_remarks = db.Column(db.String(200), nullable=True)

    total_deductions = db.Column(db.Numeric(10, 2), default=0)
    net_salary = db.Column(db.Numeric(10, 2), default=0)

    # Employer contributions (not deducted from salary)
    pf_employer_epf = db.Column(db.Numeric(10, 2), default=0)    # 3.67% of pf_wage_base
    pf_employer_eps = db.Column(db.Numeric(10, 2), default=0)    # 8.33% (capped ₹1,250)
    pf_employer_edli = db.Column(db.Numeric(10, 2), default=0)   # 0.5% admin
    pf_employer_total = db.Column(db.Numeric(10, 2), default=0)  # Total employer PF (13%)
    esic_employer = db.Column(db.Numeric(10, 2), default=0)      # 3.25% of gross
    lwf_employer = db.Column(db.Numeric(10, 2), default=0)       # ₹12 in Jun/Dec
    gratuity = db.Column(db.Numeric(10, 2), default=0)           # 4.81% of basic (employer liability)

    # Other pay components
    bonus = db.Column(db.Numeric(10, 2), default=0)              # Statutory bonus (8.33% of basic)

    # CTC
    ctc = db.Column(db.Numeric(10, 2), default=0)  # gross + all employer contributions

    # Status
    status = db.Column(db.String(20), default='draft')  # draft, processed, paid
    processed_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    employee = db.relationship('Employee', back_populates='salary_records')
    processor = db.relationship('User', foreign_keys=[processed_by])

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year', name='uq_salary_month_year'),
    )

    @property
    def period_label(self):
        from calendar import month_name
        return f'{month_name[self.month]} {self.year}'

    @property
    def extra_earned(self):
        """Incentive / overtime / bonus — anything beyond the standard salary components."""
        return max(0.0,
            float(self.gross_earned or 0)
            - float(self.basic or 0) - float(self.hra or 0)
            - float(self.da or 0) - float(self.special_allowance or 0)
            - float(self.other_allowance or 0) - float(self.conveyance or 0)
            - float(self.medical_allowance or 0) - float(self.petrol_allowance or 0))

    def __repr__(self):
        return f'<SalaryRecord emp={self.employee_id} {self.month}/{self.year}>'


class PayrollLock(db.Model):
    __tablename__ = 'payroll_locks'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_locked = db.Column(db.Boolean, default=True, nullable=False)
    locked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    locked_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('company_id', 'month', 'year', name='uq_payroll_lock'),
    )
