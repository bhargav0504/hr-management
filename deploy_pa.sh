#!/bin/bash
set -e
PA_USER=$(whoami)
PROJECT_DIR="$HOME/hr-management"

echo "=== HR Management — PythonAnywhere Setup ==="

# Clone or update repo
if [ -d "$PROJECT_DIR" ]; then
    echo "Updating existing repo..."
    cd "$PROJECT_DIR" && git pull
else
    echo "Cloning repo..."
    git clone https://github.com/bhargav0504/hr-management.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Create virtualenv
python3 -m venv venv
source venv/bin/activate

# Install dependencies (skip PyMySQL since we use SQLite on PA)
pip install --quiet flask flask-sqlalchemy flask-login flask-migrate flask-wtf \
    wtforms werkzeug reportlab openpyxl python-dateutil email-validator \
    python-dotenv gunicorn

# Initialize database
python init_db.py

echo ""
echo "============================================"
echo "Setup done! Now follow these steps:"
echo ""
echo "1. Go to the 'Web' tab on PythonAnywhere"
echo "2. Click 'Add a new web app' → Manual config → Python 3.11"
echo "3. Source code: /home/$PA_USER/hr-management"
echo "4. Virtualenv:  /home/$PA_USER/hr-management/venv"
echo "5. Click the WSGI file link and REPLACE its contents with:"
echo ""
echo "   import sys, os"
echo "   sys.path.insert(0, '/home/$PA_USER/hr-management')"
echo "   os.environ['SECRET_KEY'] = 'change-this-secret'"
echo "   from run import app as application"
echo ""
echo "6. Click Save, then click the green Reload button"
echo "7. Your app is live at: https://$PA_USER.pythonanywhere.com"
echo "   Login: admin / Admin@123"
echo "============================================"
