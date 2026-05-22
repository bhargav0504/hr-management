import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.company import Company
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

company_bp = Blueprint('company', __name__, url_prefix='/company')

LOGO_FOLDER = os.path.join('app', 'static', 'uploads', 'logos')
ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


class CompanyForm(FlaskForm):
    name = StringField('Company Name *', validators=[DataRequired(), Length(1, 200)])
    short_name = StringField('Short Name', validators=[Optional(), Length(max=50)])
    address = TextAreaField('Address', validators=[Optional()])
    pan = StringField('PAN', validators=[Optional(), Length(max=10)])
    tan = StringField('TAN', validators=[Optional(), Length(max=10)])
    gst = StringField('GST Number', validators=[Optional(), Length(max=15)])
    pf_no = StringField('PF Registration No.', validators=[Optional(), Length(max=50)])
    esic_no = StringField('ESIC Registration No.', validators=[Optional(), Length(max=20)])
    pt_no = StringField('PT Registration No.', validators=[Optional(), Length(max=20)])
    lwf_applicable = BooleanField('Gujarat LWF Applicable', default=True)
    esic_ceiling = DecimalField('ESIC Wage Ceiling (₹)', default=21000, validators=[Optional(), NumberRange(min=0)], places=2)
    pf_wage_ceiling = DecimalField('PF Wage Ceiling (₹)', default=15000, validators=[Optional(), NumberRange(min=0)], places=2)
    pt_threshold = DecimalField('PT Threshold Gross (₹)', default=12000, validators=[Optional(), NumberRange(min=0)], places=2)
    pt_amount = DecimalField('PT Monthly Amount (₹)', default=200, validators=[Optional(), NumberRange(min=0)], places=2)
    is_active = BooleanField('Active', default=True)
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
    for f in ['name', 'short_name', 'address', 'pan', 'tan', 'gst',
              'pf_no', 'esic_no', 'pt_no', 'lwf_applicable',
              'esic_ceiling', 'pf_wage_ceiling', 'pt_threshold', 'pt_amount', 'is_active']:
        setattr(company, f, getattr(form, f).data)
