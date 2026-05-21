from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
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

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.employees import employees_bp
    from app.routes.payroll import payroll_bp
    from app.routes.advances import advances_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(advances_bp)
    app.register_blueprint(reports_bp)

    # Template filters
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
