"""Run once to create tables and an initial admin user."""
from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
from app.models.advance import Advance, AdvanceRepayment

app = create_app()

with app.app_context():
    db.create_all()
    print('Tables created.')

    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@company.com', role='admin')
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: username=admin  password=Admin@123')
        print('IMPORTANT: Change the default password after first login!')
    else:
        print('Admin user already exists.')
