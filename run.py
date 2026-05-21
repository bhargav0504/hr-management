from app import create_app, db
from app.models.user import User
from app.models.employee import Employee
from app.models.payroll import SalaryRecord
from app.models.advance import Advance

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Employee=Employee, SalaryRecord=SalaryRecord, Advance=Advance)

if __name__ == '__main__':
    app.run(debug=True)
