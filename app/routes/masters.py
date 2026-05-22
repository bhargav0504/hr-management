from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from app import db
from app.models.masters import Department, Designation, Category, Location
from app.models.leave import LeaveType

masters_bp = Blueprint('masters', __name__, url_prefix='/masters')

_MODEL_MAP = {
    'departments':  (Department,  'department',  'departments'),
    'designations': (Designation, 'designation', 'designations'),
    'categories':   (Category,    'category',    'categories'),
    'locations':    (Location,    'location',    'locations'),
}


def _get_company_id():
    return session.get('company_id')


@masters_bp.route('/')
@login_required
def index():
    cid = _get_company_id()
    return render_template('masters/index.html',
        dept_count=Department.query.filter_by(company_id=cid).count(),
        desig_count=Designation.query.filter_by(company_id=cid).count(),
        cat_count=Category.query.filter_by(company_id=cid).count(),
        loc_count=Location.query.filter_by(company_id=cid).count(),
        lt_count=LeaveType.query.filter_by(company_id=cid).count(),
    )


@masters_bp.route('/<master_type>')
@login_required
def list_master(master_type):
    if master_type not in _MODEL_MAP:
        flash('Invalid master type.', 'danger')
        return redirect(url_for('masters.index'))
    model, singular, plural = _MODEL_MAP[master_type]
    items = model.query.filter_by(company_id=_get_company_id()).order_by(model.name).all()
    return render_template('masters/list.html', items=items,
                           master_type=master_type, singular=singular,
                           title=master_type.replace('_', ' ').title(),
                           show_type=(master_type == 'categories'))


@masters_bp.route('/<master_type>/add', methods=['POST'])
@login_required
def add_master(master_type):
    if master_type not in _MODEL_MAP:
        return redirect(url_for('masters.index'))
    model, singular, plural = _MODEL_MAP[master_type]
    name = request.form.get('name', '').strip()
    cid = _get_company_id()
    if name:
        if not model.query.filter_by(company_id=cid, name=name).first():
            obj = model(company_id=cid, name=name)
            if master_type == 'categories':
                obj.type = request.form.get('type', 'staff')
            db.session.add(obj)
            db.session.commit()
            flash(f'"{name}" added.', 'success')
        else:
            flash(f'"{name}" already exists.', 'warning')
    return redirect(url_for('masters.list_master', master_type=master_type))


@masters_bp.route('/<master_type>/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_master(master_type, item_id):
    if master_type not in _MODEL_MAP:
        return redirect(url_for('masters.index'))
    model, _, __ = _MODEL_MAP[master_type]
    item = model.query.get_or_404(item_id)
    item.is_active = not item.is_active
    db.session.commit()
    return redirect(url_for('masters.list_master', master_type=master_type))


@masters_bp.route('/<master_type>/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_master(master_type, item_id):
    if master_type not in _MODEL_MAP:
        return redirect(url_for('masters.index'))
    model, _, __ = _MODEL_MAP[master_type]
    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('masters.list_master', master_type=master_type))


# ── Leave Types (kept separate — different fields) ───────────────────────────

@masters_bp.route('/leave-types')
@login_required
def leave_types():
    items = LeaveType.query.filter_by(company_id=_get_company_id()).order_by(LeaveType.code).all()
    return render_template('masters/leave_types.html', items=items)


@masters_bp.route('/leave-types/add', methods=['POST'])
@login_required
def add_leave_type():
    cid = _get_company_id()
    code = request.form.get('code', '').strip().upper()
    name = request.form.get('name', '').strip()
    days = int(request.form.get('days_per_year', 0) or 0)
    carry = int(request.form.get('carry_forward_max', 0) or 0)
    is_paid = request.form.get('is_paid') == 'on'
    if code and name:
        if not LeaveType.query.filter_by(company_id=cid, code=code).first():
            db.session.add(LeaveType(company_id=cid, code=code, name=name,
                                     days_per_year=days, carry_forward_max=carry, is_paid=is_paid))
            db.session.commit()
            flash(f'Leave type "{code}" added.', 'success')
        else:
            flash('Leave code already exists.', 'warning')
    return redirect(url_for('masters.leave_types'))


@masters_bp.route('/leave-types/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_leave_type(item_id):
    item = LeaveType.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('masters.leave_types'))

# Convenience aliases used in sidebar/base template
@masters_bp.route('/departments')
@login_required
def departments():
    return list_master('departments')

@masters_bp.route('/designations')
@login_required
def designations():
    return list_master('designations')

@masters_bp.route('/categories')
@login_required
def categories():
    return list_master('categories')

@masters_bp.route('/locations')
@login_required
def locations():
    return list_master('locations')
