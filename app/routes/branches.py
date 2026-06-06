from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.models.branch import Branch

branches_bp = Blueprint('branches', __name__, url_prefix='/branches')


def _cid():
    return session.get('company_id')


@branches_bp.route('/')
@login_required
def list_branches():
    branches = Branch.query.filter_by(company_id=_cid()).order_by(Branch.name).all()
    return render_template('branches/list.html', branches=branches)


@branches_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_branch():
    if request.method == 'POST':
        br = Branch(
            company_id=_cid(),
            name=request.form.get('name', '').strip(),
            address=request.form.get('address', '').strip(),
            state=request.form.get('state', '').strip(),
            city=request.form.get('city', '').strip(),
            pin=request.form.get('pin', '').strip(),
            email=request.form.get('email', '').strip(),
            phone=request.form.get('phone', '').strip(),
            contact_person=request.form.get('contact_person', '').strip(),
            contact_phone=request.form.get('contact_phone', '').strip(),
            contact_email=request.form.get('contact_email', '').strip(),
        )
        if not br.name:
            flash('Branch name is required.', 'danger')
            return render_template('branches/form.html', branch=None, title='Add Branch')
        db.session.add(br)
        db.session.commit()
        flash(f'Branch "{br.name}" created.', 'success')
        return redirect(url_for('branches.list_branches'))
    return render_template('branches/form.html', branch=None, title='Add Branch')


@branches_bp.route('/<int:br_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_branch(br_id):
    br = Branch.query.filter_by(id=br_id, company_id=_cid()).first_or_404()
    if request.method == 'POST':
        br.name = request.form.get('name', '').strip()
        br.address = request.form.get('address', '').strip()
        br.state = request.form.get('state', '').strip()
        br.city = request.form.get('city', '').strip()
        br.pin = request.form.get('pin', '').strip()
        br.email = request.form.get('email', '').strip()
        br.phone = request.form.get('phone', '').strip()
        br.contact_person = request.form.get('contact_person', '').strip()
        br.contact_phone = request.form.get('contact_phone', '').strip()
        br.contact_email = request.form.get('contact_email', '').strip()
        db.session.commit()
        flash('Branch updated.', 'success')
        return redirect(url_for('branches.list_branches'))
    return render_template('branches/form.html', branch=br, title='Edit Branch')


@branches_bp.route('/<int:br_id>/toggle', methods=['POST'])
@login_required
def toggle_branch(br_id):
    br = Branch.query.filter_by(id=br_id, company_id=_cid()).first_or_404()
    br.is_active = not br.is_active
    db.session.commit()
    flash(f'Branch {"activated" if br.is_active else "deactivated"}.', 'success')
    return redirect(url_for('branches.list_branches'))


@branches_bp.route('/<int:br_id>/delete', methods=['POST'])
@login_required
def delete_branch(br_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('branches.list_branches'))
    br = Branch.query.filter_by(id=br_id, company_id=_cid()).first_or_404()
    db.session.delete(br)
    db.session.commit()
    flash('Branch deleted.', 'success')
    return redirect(url_for('branches.list_branches'))
