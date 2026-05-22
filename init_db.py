"""Run once to create tables and seed initial data. Use --reset to drop and recreate."""
import sys
from app import create_app, db
from app.models.user import User
from app.models.company import Company
from app.models.masters import Department, Designation, Category, Location
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
from app.models.advance import Advance, AdvanceRepayment
from app.models.family import EmployeeFamily
from app.models.leave import LeaveType, LeaveBalance, LeaveApplication

app = create_app()

with app.app_context():
    if '--reset' in sys.argv:
        print('Dropping all tables...')
        db.drop_all()
        print('Dropped.')

    db.create_all()
    print('Tables created.')

    # ── Default admin user ────────────────────────────────────────────────────
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@company.com', role='admin')
        admin.set_password('Admin@123')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created: username=admin  password=Admin@123')
        print('IMPORTANT: Change the default password after first login!')
    else:
        print('Admin user already exists.')

    # ── Default company ───────────────────────────────────────────────────────
    if not Company.query.first():
        company = Company(
            name='Demo Company Pvt. Ltd.',
            short_name='Demo Co.',
            address='Ahmedabad, Gujarat, India',
            pf_no='GJ/AHD/0000000/000/000001',
            esic_no='41000000000000000',
            pt_no='GJ-PT-000000',
            lwf_applicable=True,
        )
        db.session.add(company)
        db.session.flush()  # get company.id

        # Default departments
        for dept_name in ['Administration', 'Accounts', 'HR', 'Operations', 'Production', 'Sales']:
            db.session.add(Department(company_id=company.id, name=dept_name))

        # Default designations
        for desig in ['Manager', 'Supervisor', 'Worker', 'Accountant', 'HR Executive', 'Director']:
            db.session.add(Designation(company_id=company.id, name=desig))

        # Default categories
        for cat_name, cat_type in [
            ('Management Staff', 'management'),
            ('Clerical Staff', 'staff'),
            ('Skilled Worker', 'worker'),
            ('Semi-Skilled Worker', 'worker'),
            ('Unskilled Worker', 'worker'),
        ]:
            db.session.add(Category(company_id=company.id, name=cat_name, type=cat_type))

        # Default locations
        for loc in ['Head Office', 'Factory', 'Branch']:
            db.session.add(Location(company_id=company.id, name=loc))

        # Default leave types (Gujarat norms)
        leave_defaults = [
            ('PL', 'Privilege Leave', 15, 30, True),
            ('SL', 'Sick Leave', 7, 0, True),
            ('CL', 'Casual Leave', 7, 0, True),
            ('ML', 'Maternity Leave', 182, 0, True),   # 26 weeks
            ('EL', 'Earned Leave', 15, 30, True),
            ('WO', 'Weekly Off', 0, 0, True),
        ]
        for code, name, days, carry, paid in leave_defaults:
            db.session.add(LeaveType(
                company_id=company.id, code=code, name=name,
                days_per_year=days, carry_forward_max=carry, is_paid=paid,
            ))

        db.session.commit()
        print(f'Default company created: "{company.name}"')
        print('Default departments, designations, categories, locations, and leave types created.')
    else:
        print('Company already exists.')

    print()
    print('Setup complete! Run: python run.py')
    print('Open: http://localhost:5000')
    print('Login: admin / Admin@123')
