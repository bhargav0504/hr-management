from app import db
from datetime import datetime


class EmployeeEducation(db.Model):
    __tablename__ = 'employee_education'
    id           = db.Column(db.Integer, primary_key=True)
    employee_id  = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    degree       = db.Column(db.String(100), nullable=False)
    passing_year = db.Column(db.String(10))
    university   = db.Column(db.String(200))
    class_grade  = db.Column(db.String(50))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='education_details')


class EmployeePrevEmployment(db.Model):
    __tablename__ = 'employee_prev_employment'
    id                   = db.Column(db.Integer, primary_key=True)
    employee_id          = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    employer_name        = db.Column(db.String(200), nullable=False)
    joining_date         = db.Column(db.Date)
    leaving_date         = db.Column(db.Date)
    joining_designation  = db.Column(db.String(100))
    leaving_designation  = db.Column(db.String(100))
    last_salary          = db.Column(db.Numeric(10, 2))
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='prev_employments')
