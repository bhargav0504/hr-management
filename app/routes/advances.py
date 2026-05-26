from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models.employee import Employee
from app.models.advance import Advance, AdvanceRepayment
from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, DateField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import date

advances_bp = Blueprint('advances', __name__, url_prefix='/advances')


def _company_id():
    return session.get('company_id')


class AdvanceForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Advance Amount (₹)', validators=[DataRequired(), NumberRange(min=1)], places=2)
    disbursed_date = DateField('Disbursed Date', validators=[DataRequired()], default=date.today)
    monthly_installment = DecimalField('Monthly Installment (₹)',
                                       validators=[DataRequired(), NumberRange(min=1)], places=2)
    reason = StringField('Reason', validators=[Optional()])
    submit = SubmitField('Grant Advance')


@advances_bp.route('/')
@login_required
def list_advances():
    cid = _company_id()
    status = request.args.get('status', 'active')
    q = request.args.get('q', '').strip()
    query = Advance.query.join(Employee).filter(Employee.company_id == cid)
    if status in ('active', 'closed'):
        query = query.filter(Advance.status == status)
    if q:
        query = query.filter(
            db.or_(
                Employee.first_name.ilike(f'%{q}%'),
                Employee.last_name.ilike(f'%{q}%'),
                Employee.emp_code.ilike(f'%{q}%'),
            )
        )
    advances = query.order_by(Advance.disbursed_date.desc()).all()
    return render_template('advances/list.html', advances=advances, status=status, q=q)


@advances_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_advance():
    cid = _company_id()
    form = AdvanceForm()
    form.employee_id.choices = [
        (e.id, f'{e.emp_code} — {e.full_name} ({e.location or "—"})')
        for e in Employee.query.filter_by(company_id=cid, is_active=True).order_by(Employee.emp_code).all()
    ]
    if form.validate_on_submit():
        # Verify employee belongs to this company
        emp = Employee.query.filter_by(id=form.employee_id.data, company_id=cid).first()
        if not emp:
            flash('Invalid employee selection.', 'danger')
            return render_template('advances/form.html', form=form, title='Grant Advance')
        advance = Advance(
            employee_id=form.employee_id.data,
            amount=form.amount.data,
            disbursed_date=form.disbursed_date.data,
            monthly_installment=form.monthly_installment.data,
            reason=form.reason.data,
            balance=form.amount.data,
            approved_by=current_user.id,
        )
        db.session.add(advance)
        db.session.commit()
        flash('Advance granted successfully.', 'success')
        return redirect(url_for('advances.list_advances'))
    return render_template('advances/form.html', form=form, title='Grant Advance')


@advances_bp.route('/<int:adv_id>')
@login_required
def detail(adv_id):
    advance = Advance.query.get_or_404(adv_id)
    # Ensure advance belongs to current company
    if advance.employee.company_id != _company_id():
        flash('Access denied.', 'danger')
        return redirect(url_for('advances.list_advances'))
    repayments = advance.repayments.order_by(
        AdvanceRepayment.year.desc(), AdvanceRepayment.month.desc()
    ).all()
    return render_template('advances/detail.html', advance=advance, repayments=repayments)


@advances_bp.route('/<int:adv_id>/close', methods=['POST'])
@login_required
def close_advance(adv_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('advances.list_advances'))
    advance = Advance.query.get_or_404(adv_id)
    if advance.employee.company_id != _company_id():
        flash('Access denied.', 'danger')
        return redirect(url_for('advances.list_advances'))
    advance.status = 'closed'
    db.session.commit()
    flash('Advance closed.', 'success')
    return redirect(url_for('advances.detail', adv_id=adv_id))
