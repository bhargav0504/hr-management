# HR Management System — Getting Started

## What You Need (Install These First)

1. **Python 3.11+** — https://www.python.org/downloads/
   - During install, check **"Add Python to PATH"**
2. **Git** — https://git-scm.com/downloads
3. **VS Code** — https://code.visualstudio.com/ (already installed)

---

## Step 1 — Get the Code

Open VS Code → open the **Terminal** (top menu: Terminal → New Terminal) and run:

```bash
git clone https://github.com/bhargav0504/hr-management.git
cd hr-management
```

---

## Step 2 — Set Up Python Environment

In the same terminal:

```bash
python -m venv venv
```

Then activate it:

- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You should see `(venv)` appear at the start of the terminal line.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Wait for it to finish (1–2 minutes).

---

## Step 4 — Set Up the Database

```bash
python init_db.py
```

You should see:
```
Tables created.
Admin user created: username=admin  password=Admin@123
```

---

## Step 5 — Run the App

```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

---

## Step 6 — Open in Browser

Go to: **http://localhost:5000**

**Login:**
- Username: `admin`
- Password: `Admin@123`

---

## Stopping the App

Press **Ctrl + C** in the terminal.

## Starting Again Next Time

You only need Steps 5 and 6 next time. Just make sure the virtual environment is activated first (Step 2 activate command).

---

## Reporting Issues

Please note down:
- What you were doing (e.g. "adding an employee", "running payroll")
- What you expected to happen
- What actually happened (screenshot or error message if any)

Send these details via WhatsApp/email so the issue can be fixed quickly.
