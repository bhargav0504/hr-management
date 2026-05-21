import sys
import os

project_home = os.path.expanduser('~/hr-management')
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault('SECRET_KEY', 'pythonanywhere-demo-key-change-me')

from run import app as application
