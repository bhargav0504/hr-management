from app import db


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='departments')

    def __repr__(self):
        return f'<Department {self.name}>'


class Designation(db.Model):
    __tablename__ = 'designations'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='designations')

    def __repr__(self):
        return f'<Designation {self.name}>'


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), default='staff')  # staff / worker / management
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='categories')

    def __repr__(self):
        return f'<Category {self.name}>'


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=True)
    state = db.Column(db.String(50), nullable=True)
    # Registration codes for this location
    pf_code = db.Column(db.String(50), nullable=True)
    esic_code = db.Column(db.String(50), nullable=True)
    pt_code = db.Column(db.String(50), nullable=True)
    lwf_code = db.Column(db.String(50), nullable=True)
    # Professional Tax — state-specific
    pt_applicable = db.Column(db.Boolean, default=True)
    pt_threshold = db.Column(db.Numeric(10, 2), default=12000)
    pt_amount = db.Column(db.Numeric(10, 2), default=200)
    # Labour Welfare Fund — state-specific
    lwf_applicable = db.Column(db.Boolean, default=True)
    lwf_employee = db.Column(db.Numeric(10, 2), default=6)
    lwf_employer = db.Column(db.Numeric(10, 2), default=12)
    lwf_months = db.Column(db.String(20), default='6,12')  # comma-separated month numbers
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='locations')

    @property
    def lwf_month_list(self):
        try:
            return [int(m.strip()) for m in (self.lwf_months or '6,12').split(',') if m.strip()]
        except ValueError:
            return [6, 12]

    def __repr__(self):
        return f'<Location {self.name}>'


class SalaryComponent(db.Model):
    __tablename__ = 'salary_components'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    component_type = db.Column(db.String(20), nullable=False, default='earning')  # earning / deduction
    is_statutory = db.Column(db.Boolean, default=False)   # PF, ESIC, PT, LWF
    is_taxable = db.Column(db.Boolean, default=True)
    is_pf_included = db.Column(db.Boolean, default=True)  # part of PF wage base
    is_esic_included = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='salary_components')

    def __repr__(self):
        return f'<SalaryComponent {self.name}>'
