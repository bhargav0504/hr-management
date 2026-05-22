from app import db


class EmployeeFamily(db.Model):
    __tablename__ = 'employee_family'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    relation = db.Column(db.String(50), nullable=False)  # Spouse, Son, Daughter, Father, Mother, Other
    date_of_birth = db.Column(db.Date, nullable=True)
    is_nominee = db.Column(db.Boolean, default=False)
    nominee_percent = db.Column(db.Integer, default=0)

    employee = db.relationship('Employee', back_populates='family_members')

    def __repr__(self):
        return f'<Family {self.name} ({self.relation})>'
