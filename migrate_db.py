"""
Run this script ONCE to add new columns to existing tables.
Safe to run on a live database — only adds columns, never drops data.

Usage:
    python migrate_db.py
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

MYSQL_MIGRATIONS = [
    # Company salary structure columns
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_basic_pct DECIMAL(5,2) DEFAULT 50",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_hra_pct DECIMAL(5,2) DEFAULT 40",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_da_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_special_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_other_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_conveyance_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_medical_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_petrol_pct DECIMAL(5,2) DEFAULT 0",
    # Company new columns
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS company_type VARCHAR(50)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS formation_date DATE",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS city VARCHAR(100)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS state VARCHAR(50)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS pin VARCHAR(10)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS phone VARCHAR(20)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS email VARCHAR(120)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS lwf_no VARCHAR(20)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS authorised_signatory VARCHAR(200)",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS manager_name VARCHAR(200)",
    # Company salary structure
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_basic_pct DECIMAL(5,2) DEFAULT 50",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_hra_pct DECIMAL(5,2) DEFAULT 40",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_da_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_special_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_other_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_conveyance_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_medical_pct DECIMAL(5,2) DEFAULT 0",
    "ALTER TABLE companies ADD COLUMN IF NOT EXISTS ss_petrol_pct DECIMAL(5,2) DEFAULT 0",
    # Location new columns
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS address TEXT",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS state VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS pf_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS esic_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS pt_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS lwf_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS pt_applicable BOOLEAN DEFAULT TRUE",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS pt_threshold DECIMAL(10,2) DEFAULT 12000",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS pt_amount DECIMAL(10,2) DEFAULT 200",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS lwf_applicable BOOLEAN DEFAULT TRUE",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS lwf_employee DECIMAL(10,2) DEFAULT 6",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS lwf_employer DECIMAL(10,2) DEFAULT 12",
    "ALTER TABLE locations ADD COLUMN IF NOT EXISTS lwf_months VARCHAR(20) DEFAULT '6,12'",
    # Employee new column
    "ALTER TABLE employees ADD COLUMN IF NOT EXISTS state VARCHAR(50)",
]

SQLITE_MIGRATIONS = [
    # Company new columns
    "ALTER TABLE companies ADD COLUMN company_type VARCHAR(50)",
    "ALTER TABLE companies ADD COLUMN formation_date DATE",
    "ALTER TABLE companies ADD COLUMN city VARCHAR(100)",
    "ALTER TABLE companies ADD COLUMN state VARCHAR(50)",
    "ALTER TABLE companies ADD COLUMN pin VARCHAR(10)",
    "ALTER TABLE companies ADD COLUMN phone VARCHAR(20)",
    "ALTER TABLE companies ADD COLUMN email VARCHAR(120)",
    "ALTER TABLE companies ADD COLUMN lwf_no VARCHAR(20)",
    "ALTER TABLE companies ADD COLUMN authorised_signatory VARCHAR(200)",
    "ALTER TABLE companies ADD COLUMN manager_name VARCHAR(200)",
    # SQLite does not support IF NOT EXISTS in ALTER TABLE
    "ALTER TABLE locations ADD COLUMN address TEXT",
    "ALTER TABLE locations ADD COLUMN state VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN pf_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN esic_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN pt_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN lwf_code VARCHAR(50)",
    "ALTER TABLE locations ADD COLUMN pt_applicable BOOLEAN DEFAULT 1",
    "ALTER TABLE locations ADD COLUMN pt_threshold DECIMAL DEFAULT 12000",
    "ALTER TABLE locations ADD COLUMN pt_amount DECIMAL DEFAULT 200",
    "ALTER TABLE locations ADD COLUMN lwf_applicable BOOLEAN DEFAULT 1",
    "ALTER TABLE locations ADD COLUMN lwf_employee DECIMAL DEFAULT 6",
    "ALTER TABLE locations ADD COLUMN lwf_employer DECIMAL DEFAULT 12",
    "ALTER TABLE locations ADD COLUMN lwf_months VARCHAR(20) DEFAULT '6,12'",
    "ALTER TABLE employees ADD COLUMN state VARCHAR(50)",
]

with app.app_context():
    uri = str(db.engine.url)
    is_sqlite = uri.startswith('sqlite')
    migrations = SQLITE_MIGRATIONS if is_sqlite else MYSQL_MIGRATIONS

    print(f'Database: {"SQLite" if is_sqlite else "MySQL"}')

    for sql in migrations:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print(f'  OK: {sql[:60]}...' if len(sql) > 60 else f'  OK: {sql}')
        except Exception as e:
            db.session.rollback()
            # Duplicate column errors are expected on re-runs
            if 'duplicate column' in str(e).lower() or '1060' in str(e):
                print(f'  SKIP (already exists): {sql[:50]}...')
            else:
                print(f'  ERROR: {e}')

    # Create new tables — safe, skips if exists
    from app.models.payroll import PayrollLock  # noqa
    from app.models.branch import Branch  # noqa
    from app.models.fnf import FnFRecord  # noqa
    from app.models.bonus import BonusRecord  # noqa
    from app.models.arrears import ArrearRecord  # noqa
    db.create_all()
    print('New tables created (payroll_locks, branches, fnf_records, bonus_records).')
    print('\nMigration complete!')
