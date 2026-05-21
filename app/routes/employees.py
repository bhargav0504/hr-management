from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from flask_wtf import FlaskForm
from wtforms import (StringField, SelectField, DecimalField, DateField,
                     BooleanField, TextAreaField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from decimal import Decimal

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')


class EmployeeForm(FlaskForm):
    emp_code = StringField('Employee Code', validators=[DataRequired(), Length(1, 20)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(1, 100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(1, 100)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    marital_status = SelectField('Marital Status', choices=[('Single', 'Single'), ('Married', 'Married')])
    father_husband_name = StringField('Father / Husband Name', validators=[Optional(), Length(max=200)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    date_of_joining = DateField('Date of Joining', validators=[DataRequired()])
    date_of_leaving = DateField('Date of Leaving', validators=[Optional()])
    department = StringField('Department', validators=[DataRequired(), Length(1, 100)])
    location = StringField('Location', validators=[Optional(), Length(max=100)], default='Head Office')
    designation = StringField('Designation', validators=[DataRequired(), Length(1, 100)])
    category = StringField('Category (Worker/Staff/Mgmt)', validators=[Optional(), Length(max=50)])
    employment_type = SelectField('Employment Type',
                                  choices=[('permanent', 'Permanent'), ('contract', 'Contract')])
    mobile = StringField('Mobile (Primary)', validators=[Optional(), Length(max=15)])
    alt_mobile = StringField('Mobile (Alternate)', validators=[Optional(), Length(max=15)])
    email = StringField('Email', validators=[Optional(), Length(max=120)])
    address = TextAreaField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    pan_number = StringField('PAN Number', validators=[Optional(), Length(max=10)])
    aadhaar_number = StringField('Aadhaar Number', validators=[Optional(), Length(max=12)])
    uan_number = StringField('UAN Number (PF)', validators=[Optional(), Length(max=12)])
    esic_ip_number = StringField('ESIC IP Number', validators=[Optional(), Length(max=17)])
    disp_no = StringField('ESIC Dispensary No.', validators=[Optional(), Length(max=20)])
    bank_account = StringField('Bank Account No.', validators=[Optional(), Length(max=20)])
    bank_name = StringField('Bank Name', validators=[Optional(), Length(max=100)])
    ifsc_code = StringField('IFSC Code', validators=[Optional(), Length(max=11)])
    gross_ctc = DecimalField('Gross CTC (Total Monthly)', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    basic_salary = DecimalField('Basic Salary', validators=[DataRequired(), NumberRange(min=0)], places=2)
    hra = DecimalField('HRA', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    da = DecimalField('DA', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    special_allowance = DecimalField('Special Allowance', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    other_allowance = DecimalField('Other Allowance', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    petrol_allowance = DecimalField('Petrol Allowance (excl. from PF)', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    conveyance = DecimalField('Conveyance', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    medical_allowance = DecimalField('Medical Allowance', validators=[Optional(), NumberRange(min=0)], places=2, default=0)
    pf_applicable = BooleanField('PF Applicable', default=True)
    pf_on_ceiling = BooleanField('PF capped at ₹15,000 wage ceiling', default=True)
    pension_eligible = BooleanField('Pension (EPS) Eligible', default=True)
    esic_applicable = BooleanField('ESIC Applicable', default=True)
    pt_applicable = BooleanField('Professional Tax (PT) Applicable', default=True)
    tds_regime = SelectField('TDS Regime', choices=[('new', 'New Regime (Default)'), ('old', 'Old Regime')])
    submit = SubmitField('Save Employee')


@employees_bp.route('/')
@login_required
def list_employees():
    show_inactive = request.args.get('inactive', 'false') == 'true'
    q = request.args.get('q', '').strip()
    dept = request.args.get('dept', '')
    query = Employee.query
    if not show_inactive:
        query = query.filter_by(is_active=True)
    if q:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f'%{q}%'),
                Employee.last_name.ilike(f'%{q}%'),
                Employee.emp_code.ilike(f'%{q}%'),
            )
        )
    if dept:
        query = query.filter_by(department=dept)
    employees = query.order_by(Employee.emp_code).all()
    departments = [r[0] for r in Employee.query.with_entities(Employee.department).distinct().all()]
    return render_template('employees/list.html', employees=employees,
                           departments=departments, show_inactive=show_inactive,
                           q=q, dept=dept)


@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        if Employee.query.filter_by(emp_code=form.emp_code.data).first():
            flash('Employee code already exists.', 'danger')
            return render_template('employees/form.html', form=form, title='Add Employee')
        emp = Employee()
        _populate_employee(emp, form)
        db.session.add(emp)
        db.session.commit()
        flash(f'Employee {emp.full_name} added successfully.', 'success')
        return redirect(url_for('employees.detail', emp_id=emp.id))
    return render_template('employees/form.html', form=form, title='Add Employee')


@employees_bp.route('/<int:emp_id>')
@login_required
def detail(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    recent_payroll = emp.salary_records.order_by(
        db.text('year desc, month desc')
    ).limit(12).all()
    active_advances = emp.advances.filter_by(status='active').all()
    return render_template('employees/detail.html', emp=emp,
                           recent_payroll=recent_payroll, active_advances=active_advances)


@employees_bp.route('/<int:emp_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    form = EmployeeForm(obj=emp)
    if form.validate_on_submit():
        existing = Employee.query.filter(
            Employee.emp_code == form.emp_code.data,
            Employee.id != emp_id
        ).first()
        if existing:
            flash('Employee code already used by another employee.', 'danger')
        else:
            _populate_employee(emp, form)
            db.session.commit()
            flash('Employee updated successfully.', 'success')
            return redirect(url_for('employees.detail', emp_id=emp.id))
    return render_template('employees/form.html', form=form, title='Edit Employee', emp=emp)


@employees_bp.route('/<int:emp_id>/toggle', methods=['POST'])
@login_required
def toggle_employee(emp_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('employees.list_employees'))
    emp = Employee.query.get_or_404(emp_id)
    emp.is_active = not emp.is_active
    db.session.commit()
    status = 'activated' if emp.is_active else 'deactivated'
    flash(f'{emp.full_name} {status}.', 'success')
    return redirect(url_for('employees.detail', emp_id=emp_id))


def _populate_employee(emp, form):
    for field in [
        'emp_code', 'first_name', 'last_name', 'gender', 'marital_status',
        'father_husband_name', 'date_of_birth', 'date_of_joining', 'date_of_leaving',
        'department', 'location', 'designation', 'category', 'employment_type',
        'mobile', 'alt_mobile', 'email', 'address', 'city',
        'pan_number', 'aadhaar_number', 'uan_number', 'esic_ip_number', 'disp_no',
        'bank_account', 'bank_name', 'ifsc_code',
        'gross_ctc', 'basic_salary', 'hra', 'da', 'special_allowance', 'other_allowance',
        'petrol_allowance', 'conveyance', 'medical_allowance',
        'pf_applicable', 'pf_on_ceiling', 'pension_eligible',
        'esic_applicable', 'pt_applicable', 'tds_regime',
    ]:
        setattr(emp, field, getattr(form, field).data)
