import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.company import Company
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, DecimalField, SelectField, DateField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

company_bp = Blueprint('company', __name__, url_prefix='/company')

LOGO_FOLDER = os.path.join('app', 'static', 'uploads', 'logos')
ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

COMPANY_TYPES = [
    ('', '— Select Type —'),
    ('Private Limited', 'Private Limited (Pvt. Ltd.)'),
    ('Public Limited', 'Public Limited (Ltd.)'),
    ('LLP', 'Limited Liability Partnership (LLP)'),
    ('Partnership', 'Partnership Firm'),
    ('Proprietorship', 'Sole Proprietorship'),
    ('OPC', 'One Person Company (OPC)'),
    ('Trust', 'Trust / NGO'),
    ('Society', 'Society / Co-operative'),
    ('Other', 'Other'),
]


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


class CompanyForm(FlaskForm):
    name = StringField('Company Name *', validators=[DataRequired(), Length(1, 200)])
    short_name = StringField('Short Name / Trade Name', validators=[Optional(), Length(max=50)])
    company_type = SelectField('Type of Company', choices=COMPANY_TYPES, validators=[Optional()])
    formation_date = DateField('Formation / Incorporation Date', validators=[Optional()])
    authorised_signatory = StringField('Authorised Signatory Name', validators=[Optional(), Length(max=200)])
    manager_name = StringField('HR / Manager Name', validators=[Optional(), Length(max=200)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Length(max=120)])
    address = TextAreaField('Registered Address', validators=[Optional()])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    state = StringField('State', validators=[Optional(), Length(max=50)])
    pin = StringField('PIN Code', validators=[Optional(), Length(max=10)])
    pan = StringField('PAN', validators=[Optional(), Length(max=10)])
    tan = StringField('TAN', validators=[Optional(), Length(max=10)])
    gst = StringField('GST Number', validators=[Optional(), Length(max=15)])
    pf_no = StringField('PF Registration No.', validators=[Optional(), Length(max=50)])
    esic_no = StringField('ESIC Registration No.', validators=[Optional(), Length(max=20)])
    pt_no = StringField('PT Registration No.', validators=[Optional(), Length(max=20)])
    lwf_no = StringField('LWF Registration No.', validators=[Optional(), Length(max=20)])
    lwf_applicable = BooleanField('LWF Applicable', default=True)
    esic_ceiling = DecimalField('ESIC Wage Ceiling (₹)', default=21000, validators=[Optional(), NumberRange(min=0)], places=2)
    pf_wage_ceiling = DecimalField('PF Wage Ceiling (₹)', default=15000, validators=[Optional(), NumberRange(min=0)], places=2)
    pt_threshold = DecimalField('PT Threshold Gross (₹)', default=12000, validators=[Optional(), NumberRange(min=0)], places=2)
    pt_amount = DecimalField('PT Monthly Amount (₹)', default=200, validators=[Optional(), NumberRange(min=0)], places=2)
    is_active = BooleanField('Active', default=True)
    # Salary structure template
    ss_basic_pct = DecimalField('Basic (% of Gross)', default=50, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_hra_pct = DecimalField('HRA (% of Basic)', default=40, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_da_pct = DecimalField('DA (% of Basic)', default=0, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_special_pct = DecimalField('Special Allow. (% of Gross)', default=0, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_other_pct = DecimalField('Other Allow. (% of Gross)', default=0, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_conveyance_pct = DecimalField('Conveyance (% of Gross)', default=0, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_medical_pct = DecimalField('Medical Allow. (% of Gross)', default=0, validators=[Optional(), NumberRange(0, 100)], places=2)
    ss_petrol_pct = DecimalField('Petrol Allow. (% of Gross)', default=0, validators=[Optional(), NumberRange(0, 100)], places=2)
    submit = SubmitField('Save Company')


@company_bp.route('/select')
@login_required
def select():
    companies = Company.query.filter_by(is_active=True).order_by(Company.name).all()
    if len(companies) == 1 and not current_user.is_admin():
        session['company_id'] = companies[0].id
        return redirect(url_for('dashboard.index'))
    if not companies:
        if current_user.is_admin():
            flash('No company found. Please create one first.', 'warning')
            return redirect(url_for('company.create_company'))
        flash('No company configured. Contact administrator.', 'danger')
    return render_template('company/select.html', companies=companies)


@company_bp.route('/switch/<int:company_id>')
@login_required
def switch(company_id):
    company = Company.query.get_or_404(company_id)
    session['company_id'] = company.id
    flash(f'Switched to {company.name}', 'success')
    return redirect(url_for('dashboard.index'))


@company_bp.route('/')
@login_required
def list_companies():
    companies = Company.query.order_by(Company.name).all()
    return render_template('company/list.html', companies=companies)


@company_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_company():
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('company.list_companies'))
    form = CompanyForm()
    if form.validate_on_submit():
        logo_filename = None
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename and _allowed(logo_file.filename):
            os.makedirs(LOGO_FOLDER, exist_ok=True)
            filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join(LOGO_FOLDER, filename))
            logo_filename = filename
        company = Company(logo_filename=logo_filename)
        _populate(company, form)
        db.session.add(company)
        db.session.commit()
        session['company_id'] = company.id
        flash(f'{company.name} created.', 'success')
        return redirect(url_for('company.list_companies'))
    return render_template('company/form.html', form=form, title='Add Company')


@company_bp.route('/<int:company_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_company(company_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('company.list_companies'))
    company = Company.query.get_or_404(company_id)
    form = CompanyForm(obj=company)
    if form.validate_on_submit():
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename and _allowed(logo_file.filename):
            os.makedirs(LOGO_FOLDER, exist_ok=True)
            filename = secure_filename(logo_file.filename)
            logo_file.save(os.path.join(LOGO_FOLDER, filename))
            company.logo_filename = filename
        _populate(company, form)
        db.session.commit()
        flash('Company updated.', 'success')
        return redirect(url_for('company.list_companies'))
    return render_template('company/form.html', form=form, title='Edit Company', company=company)


def _populate(company, form):
    for f in ['name', 'short_name', 'company_type', 'formation_date',
              'authorised_signatory', 'manager_name', 'phone', 'email',
              'address', 'city', 'state', 'pin',
              'pan', 'tan', 'gst', 'pf_no', 'esic_no', 'pt_no', 'lwf_no',
              'lwf_applicable', 'esic_ceiling', 'pf_wage_ceiling',
              'pt_threshold', 'pt_amount', 'is_active',
              'ss_basic_pct', 'ss_hra_pct', 'ss_da_pct', 'ss_special_pct',
              'ss_other_pct', 'ss_conveyance_pct', 'ss_medical_pct', 'ss_petrol_pct']:
        setattr(company, f, getattr(form, f).data)


@company_bp.route('/salary-structure/<int:company_id>')
@login_required
def get_salary_structure(company_id):
    """JSON endpoint — returns salary structure percentages for the given company."""
    from flask import jsonify
    company = Company.query.get_or_404(company_id)
    return jsonify({
        'ss_basic_pct': float(company.ss_basic_pct or 50),
        'ss_hra_pct': float(company.ss_hra_pct or 40),
        'ss_da_pct': float(company.ss_da_pct or 0),
        'ss_special_pct': float(company.ss_special_pct or 0),
        'ss_other_pct': float(company.ss_other_pct or 0),
        'ss_conveyance_pct': float(company.ss_conveyance_pct or 0),
        'ss_medical_pct': float(company.ss_medical_pct or 0),
        'ss_petrol_pct': float(company.ss_petrol_pct or 0),
    })
