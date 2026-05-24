from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from app import db
from app.models.masters import Department, Designation, Category, Location, SalaryComponent
from app.models.leave import LeaveType

masters_bp = Blueprint('masters', __name__, url_prefix='/masters')

# Generic masters (name-only) — Location is handled separately
_MODEL_MAP = {
    'departments':  (Department,  'department',  'departments'),
    'designations': (Designation, 'designation', 'designations'),
    'categories':   (Category,    'category',    'categories'),
}

INDIAN_STATES = [
    '', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman & Nicobar Islands', 'Chandigarh', 'Dadra & Nagar Haveli', 'Daman & Diu',
    'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry',
]

# PT defaults by state (threshold, amount)
PT_STATE_DEFAULTS = {
    'Gujarat':       (12000, 200),
    'Maharashtra':   (10000, 200),
    'Karnataka':     (15000, 200),
    'Tamil Nadu':    (21000, 208),
    'West Bengal':   (10000, 200),
    'Andhra Pradesh':(15000, 200),
    'Telangana':     (15000, 200),
    'Madhya Pradesh':(18750, 208),
    'Odisha':        (15000, 200),
    'Kerala':        (12000, 208),
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
        sc_count=SalaryComponent.query.filter_by(company_id=cid).count(),
    )


# ── Generic masters (Dept / Desig / Category) ────────────────────────────────

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


# ── Location master (separate — has many fields) ─────────────────────────────

@masters_bp.route('/locations')
@login_required
def list_locations():
    items = Location.query.filter_by(company_id=_get_company_id()).order_by(Location.name).all()
    return render_template('masters/location_list.html', items=items, states=INDIAN_STATES)


@masters_bp.route('/locations/add', methods=['POST'])
@login_required
def add_location():
    cid = _get_company_id()
    name = request.form.get('name', '').strip()
    if not name:
        flash('Location name is required.', 'danger')
        return redirect(url_for('masters.list_locations'))
    if Location.query.filter_by(company_id=cid, name=name).first():
        flash(f'"{name}" already exists.', 'warning')
        return redirect(url_for('masters.list_locations'))
    loc = Location(
        company_id=cid,
        name=name,
        address=request.form.get('address', '').strip() or None,
        state=request.form.get('state', '').strip() or None,
        pf_code=request.form.get('pf_code', '').strip() or None,
        esic_code=request.form.get('esic_code', '').strip() or None,
        pt_code=request.form.get('pt_code', '').strip() or None,
        lwf_code=request.form.get('lwf_code', '').strip() or None,
        pt_applicable=request.form.get('pt_applicable') == 'on',
        pt_threshold=float(request.form.get('pt_threshold', 12000) or 12000),
        pt_amount=float(request.form.get('pt_amount', 200) or 200),
        lwf_applicable=request.form.get('lwf_applicable') == 'on',
        lwf_employee=float(request.form.get('lwf_employee', 6) or 6),
        lwf_employer=float(request.form.get('lwf_employer', 12) or 12),
        lwf_months=request.form.get('lwf_months', '6,12').strip() or '6,12',
    )
    db.session.add(loc)
    db.session.commit()
    flash(f'Location "{name}" added.', 'success')
    return redirect(url_for('masters.list_locations'))


@masters_bp.route('/locations/<int:loc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_location(loc_id):
    loc = Location.query.get_or_404(loc_id)
    if request.method == 'POST':
        loc.name = request.form.get('name', '').strip() or loc.name
        loc.address = request.form.get('address', '').strip() or None
        loc.state = request.form.get('state', '').strip() or None
        loc.pf_code = request.form.get('pf_code', '').strip() or None
        loc.esic_code = request.form.get('esic_code', '').strip() or None
        loc.pt_code = request.form.get('pt_code', '').strip() or None
        loc.lwf_code = request.form.get('lwf_code', '').strip() or None
        loc.pt_applicable = request.form.get('pt_applicable') == 'on'
        loc.pt_threshold = float(request.form.get('pt_threshold', 12000) or 12000)
        loc.pt_amount = float(request.form.get('pt_amount', 200) or 200)
        loc.lwf_applicable = request.form.get('lwf_applicable') == 'on'
        loc.lwf_employee = float(request.form.get('lwf_employee', 6) or 6)
        loc.lwf_employer = float(request.form.get('lwf_employer', 12) or 12)
        loc.lwf_months = request.form.get('lwf_months', '6,12').strip() or '6,12'
        db.session.commit()
        flash('Location updated.', 'success')
        return redirect(url_for('masters.list_locations'))
    return render_template('masters/location_form.html', loc=loc, states=INDIAN_STATES)


@masters_bp.route('/locations/<int:loc_id>/toggle', methods=['POST'])
@login_required
def toggle_location(loc_id):
    loc = Location.query.get_or_404(loc_id)
    loc.is_active = not loc.is_active
    db.session.commit()
    return redirect(url_for('masters.list_locations'))


@masters_bp.route('/locations/<int:loc_id>/delete', methods=['POST'])
@login_required
def delete_location(loc_id):
    loc = Location.query.get_or_404(loc_id)
    db.session.delete(loc)
    db.session.commit()
    flash('Location deleted.', 'success')
    return redirect(url_for('masters.list_locations'))


# ── Salary Components ─────────────────────────────────────────────────────────

@masters_bp.route('/salary-components')
@login_required
def salary_components():
    items = SalaryComponent.query.filter_by(company_id=_get_company_id()).order_by(
        SalaryComponent.component_type, SalaryComponent.name).all()
    return render_template('masters/salary_components.html', items=items)


@masters_bp.route('/salary-components/add', methods=['POST'])
@login_required
def add_salary_component():
    cid = _get_company_id()
    name = request.form.get('name', '').strip()
    if not name:
        flash('Component name is required.', 'danger')
        return redirect(url_for('masters.salary_components'))
    sc = SalaryComponent(
        company_id=cid,
        name=name,
        component_type=request.form.get('component_type', 'earning'),
        is_statutory=request.form.get('is_statutory') == 'on',
        is_taxable=request.form.get('is_taxable') == 'on',
        is_pf_included=request.form.get('is_pf_included') == 'on',
        is_esic_included=request.form.get('is_esic_included') == 'on',
    )
    db.session.add(sc)
    db.session.commit()
    flash(f'"{name}" added.', 'success')
    return redirect(url_for('masters.salary_components'))


@masters_bp.route('/salary-components/<int:sc_id>/toggle', methods=['POST'])
@login_required
def toggle_salary_component(sc_id):
    sc = SalaryComponent.query.get_or_404(sc_id)
    sc.is_active = not sc.is_active
    db.session.commit()
    return redirect(url_for('masters.salary_components'))


@masters_bp.route('/salary-components/<int:sc_id>/delete', methods=['POST'])
@login_required
def delete_salary_component(sc_id):
    sc = SalaryComponent.query.get_or_404(sc_id)
    db.session.delete(sc)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('masters.salary_components'))


# ── Leave Types ───────────────────────────────────────────────────────────────

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


# ── Convenience aliases used in sidebar ──────────────────────────────────────

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


@masters_bp.route('/locations-alias')
@login_required
def locations():
    return redirect(url_for('masters.list_locations'))
