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
    # staff / worker / management — affects minimum wage slab
    type = db.Column(db.String(20), default='staff')
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='categories')

    def __repr__(self):
        return f'<Category {self.name}>'


class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    company = db.relationship('Company', back_populates='locations')

    def __repr__(self):
        return f'<Location {self.name}>'
