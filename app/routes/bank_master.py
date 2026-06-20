from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required
from app import db
from app.models.bank import Bank, BankBranch

bank_master_bp = Blueprint('bank_master', __name__, url_prefix='/masters/banks')


def _cid():
    return session.get('company_id')


@bank_master_bp.route('/')
@login_required
def index():
    banks = Bank.query.filter_by(company_id=_cid()).order_by(Bank.name).all()
    branches = BankBranch.query.filter_by(company_id=_cid()).order_by(BankBranch.branch_name).all()
    return render_template('masters/bank_master.html', banks=banks, branches=branches)


# ── Banks ─────────────────────────────────────────────────────────────────────

@bank_master_bp.route('/add-bank', methods=['POST'])
@login_required
def add_bank():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Bank name is required.', 'danger')
        return redirect(url_for('bank_master.index'))
    if Bank.query.filter_by(company_id=_cid(), name=name).first():
        flash(f'Bank "{name}" already exists.', 'warning')
        return redirect(url_for('bank_master.index'))
    db.session.add(Bank(company_id=_cid(), name=name))
    db.session.commit()
    flash(f'Bank "{name}" added.', 'success')
    return redirect(url_for('bank_master.index'))


@bank_master_bp.route('/bank/<int:bank_id>/toggle', methods=['POST'])
@login_required
def toggle_bank(bank_id):
    bank = Bank.query.get_or_404(bank_id)
    bank.is_active = not bank.is_active
    db.session.commit()
    return redirect(url_for('bank_master.index'))


@bank_master_bp.route('/bank/<int:bank_id>/delete', methods=['POST'])
@login_required
def delete_bank(bank_id):
    bank = Bank.query.get_or_404(bank_id)
    db.session.delete(bank)
    db.session.commit()
    flash('Bank deleted.', 'success')
    return redirect(url_for('bank_master.index'))


# ── Bank Branches ─────────────────────────────────────────────────────────────

@bank_master_bp.route('/add-branch', methods=['POST'])
@login_required
def add_branch():
    cid = _cid()
    bank_id = request.form.get('bank_id', type=int)
    branch_name = request.form.get('branch_name', '').strip()
    if not bank_id or not branch_name:
        flash('Bank and branch name are required.', 'danger')
        return redirect(url_for('bank_master.index'))
    db.session.add(BankBranch(
        bank_id=bank_id,
        company_id=cid,
        branch_name=branch_name,
        address=request.form.get('address', '').strip() or None,
        ifsc_code=request.form.get('ifsc_code', '').strip().upper() or None,
    ))
    db.session.commit()
    flash(f'Branch "{branch_name}" added.', 'success')
    return redirect(url_for('bank_master.index'))


@bank_master_bp.route('/branch/<int:branch_id>/delete', methods=['POST'])
@login_required
def delete_branch(branch_id):
    branch = BankBranch.query.get_or_404(branch_id)
    db.session.delete(branch)
    db.session.commit()
    flash('Branch deleted.', 'success')
    return redirect(url_for('bank_master.index'))


# ── AJAX: list banks for dropdown ─────────────────────────────────────────────

@bank_master_bp.route('/list-json')
@login_required
def list_json():
    banks = Bank.query.filter_by(company_id=_cid(), is_active=True).order_by(Bank.name).all()
    return jsonify([{'id': b.id, 'name': b.name} for b in banks])
