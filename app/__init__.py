from flask import Flask, session, redirect, url_for, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.employees import employees_bp
    from app.routes.payroll import payroll_bp
    from app.routes.advances import advances_bp
    from app.routes.reports import reports_bp
    from app.routes.company import company_bp
    from app.routes.masters import masters_bp
    from app.routes.leave import leave_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(advances_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(masters_bp)
    app.register_blueprint(leave_bp)

    # ── Company guard: require company selection after login ──────────────────
    EXEMPT_ENDPOINTS = {
        'auth.login', 'auth.logout', 'auth.users', 'auth.create_user', 'auth.edit_user',
        'company.select', 'company.switch', 'company.create_company', 'company.list_companies',
        'company.edit_company',
    }

    @app.before_request
    def require_company():
        if not current_user.is_authenticated:
            return
        if request.endpoint is None:
            return
        if request.endpoint == 'static':
            return
        if request.endpoint in EXEMPT_ENDPOINTS:
            return
        if not session.get('company_id'):
            return redirect(url_for('company.select'))

    # ── Active company context processor ─────────────────────────────────────
    @app.context_processor
    def inject_company():
        company = None
        cid = session.get('company_id')
        if cid:
            from app.models.company import Company
            company = Company.query.get(cid)
        return dict(active_company=company)

    # ── Template filters ──────────────────────────────────────────────────────
    @app.template_filter('inr')
    def inr_format(value):
        try:
            v = float(value)
            return f'₹{v:,.2f}'
        except (TypeError, ValueError):
            return '₹0.00'

    @app.template_filter('month_name')
    def month_name_filter(value):
        from calendar import month_name as mn
        try:
            return mn[int(value)]
        except (IndexError, TypeError, ValueError):
            return str(value)

    return app
