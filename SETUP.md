# HR Management System — Setup Guide

## Prerequisites

- **Python 3.11+** — https://www.python.org/downloads/
  - During install, check **"Add Python to PATH"**
- **Git** — https://git-scm.com/downloads *(only if cloning from GitHub)*

> No database installation needed — the app uses SQLite (built into Python).

---

## Installation

### Option A — From ZIP file

1. Extract the ZIP to a folder (e.g. `hr-management`)
2. Open that folder in VS Code
3. Open the Terminal (Terminal → New Terminal) and run the steps below

### Option B — From GitHub

```bash
git clone https://github.com/bhargav0504/hr-management.git
cd hr-management
```

---

## Setup Steps

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create database and default admin user
python init_db.py
```

After Step 4 you should see:
```
Tables created.
Admin user created: username=admin  password=Admin@123
```

---

## Run

```bash
python run.py
```

Open **http://localhost:5000** in your browser.

**Default login:** `admin` / `Admin@123`

---

## Using MySQL Instead of SQLite (Optional)

If you prefer MySQL (XAMPP etc.), set the `DATABASE_URL` in a `.env` file:

```bash
copy .env.example .env
```

Edit `.env` and set:
```
DATABASE_URL=mysql+pymysql://root:@localhost:3306/hr_management
```

Create the database in MySQL first:
```sql
CREATE DATABASE hr_management;
```

Then run `python init_db.py` as above.

---

## Features

| Module | What it does |
|---|---|
| Employees | Add/edit employees with statutory IDs (PAN, Aadhaar, UAN, ESIC) |
| Payroll Run | One-click payroll for all active employees with per-employee day entry |
| Salary Sheet | View + export monthly salary register as Excel |
| PF Challan | ECR-style PF challan with EPF/EPS/EDLI breakdown |
| ESIC Challan | Monthly ESIC challan (only employees with gross ≤ ₹21,000) |
| TDS | Projected annual tax — new/old regime — monthly distribution |
| Gujarat LWF | Auto-deducted ₹6/₹12 in June & December payroll |
| Advances | Grant, track, auto-deduct installments each payroll |
| PDF Payslip | Branded payslip with PT, Gratuity, Bonus, CTC sections |
| TDS Summary | FY-wise per-employee TDS totals — export for Form 16 prep |
| PT Challan | Gujarat Professional Tax monthly challan export |
| Gratuity | 4.81% of basic shown in CTC calculation |
| Bonus | 8.33% of basic (statutory bonus) shown in payslip & CTC |

---

## Payroll Calculation Rules (FY 2024-25)

### PF
- Employee: 12% of Basic
- Employer EPF: 3.67% of Basic
- Employer EPS: 8.33% of Basic (capped at ₹1,250 if Basic > ₹15,000)
- Employer EDLI admin: 0.5% of Basic

### ESIC
- Applicable only if Gross Salary ≤ ₹21,000/month
- Employee: 0.75% of Gross
- Employer: 3.25% of Gross

### Professional Tax (PT) — Gujarat
- ₹200/month deducted if monthly gross earned ≥ ₹12,000
- Separate PT challan export available
- Set `pt_applicable = False` on employee to exclude (e.g. Directors)

### Gujarat LWF
- Deducted in June and December payroll only
- Employee: ₹6 | Employer: ₹12

### TDS — New Regime (default)
- Standard deduction ₹75,000
- Rebate u/s 87A: No tax if taxable income ≤ ₹7,00,000
- Slabs: 0% / 5% / 10% / 15% / 20% / 30%
- Health & Education Cess: 4%

### TDS — Old Regime
- Standard deduction ₹50,000
- PF employee contribution deducted from taxable income
- Rebate u/s 87A: No tax if taxable income ≤ ₹5,00,000
