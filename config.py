import os
from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hr-mgmt-secret-change-in-prod')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(_BASE_DIR, "hr_management.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Company defaults
    COMPANY_NAME = os.environ.get('COMPANY_NAME', 'Your Company Name')
    COMPANY_ADDRESS = os.environ.get('COMPANY_ADDRESS', 'Gujarat, India')
    COMPANY_PAN = os.environ.get('COMPANY_PAN', '')
    COMPANY_TAN = os.environ.get('COMPANY_TAN', '')
    COMPANY_PF_NO = os.environ.get('COMPANY_PF_NO', '')
    COMPANY_ESIC_NO = os.environ.get('COMPANY_ESIC_NO', '')
    COMPANY_PT_NO = os.environ.get('COMPANY_PT_NO', '')   # Gujarat PT registration

    # Gujarat LWF — deducted in June and December
    LWF_MONTHS = [6, 12]
    LWF_EMPLOYEE = 6      # ₹6 per period
    LWF_EMPLOYER = 12     # ₹12 per period

    # ESIC eligibility ceiling
    ESIC_CEILING = 21000

    # PF wage ceiling for EPS (₹15,000 basic)
    PF_WAGE_CEILING = 15000
    EPS_MAX = 1250          # 8.33% of 15,000
