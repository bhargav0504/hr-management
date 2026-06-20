from app import db
from datetime import datetime


class Bank(db.Model):
    __tablename__ = 'banks'
    id         = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    branches = db.relationship('BankBranch', back_populates='bank', cascade='all,delete-orphan')

    def __repr__(self):
        return f'<Bank {self.name}>'


class BankBranch(db.Model):
    __tablename__ = 'bank_branches'
    id          = db.Column(db.Integer, primary_key=True)
    bank_id     = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    company_id  = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)
    address     = db.Column(db.Text)
    ifsc_code   = db.Column(db.String(20))
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    bank = db.relationship('Bank', back_populates='branches')

    def __repr__(self):
        return f'<BankBranch {self.branch_name}>'
