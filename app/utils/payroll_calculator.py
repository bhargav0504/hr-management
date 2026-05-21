"""
Indian payroll calculation engine — matches April'26 salary sheet structure.

PF    : Employee 12% of pf_wage_base (basic+HRA+other, excl. petrol) — capped at ₹15,000 if pf_on_ceiling
        Employer: EPF 3.67% + EPS 8.33% (capped ₹1,250) + EDLI 0.5%
ESIC  : Employee 0.75% | Employer 3.25% — only if gross_earned ≤ ₹21,000
PT    : Gujarat Professional Tax — ₹200/month if gross_earned ≥ ₹12,000
LWF   : Gujarat — ₹6 employee / ₹12 employer — June & December only
Gratuity: 4.81% of basic (employer liability, not deducted from salary)
Bonus : 8.33% of basic (statutory bonus)
CTC   : gross_earned + employer PF + employer ESIC + gratuity
TDS   : Projected annual income method, new or old regime (FY 2024-25)
"""

from decimal import Decimal, ROUND_HALF_UP
import calendar as _cal


def _d(value):
    return Decimal(str(value or 0))


def _round2(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _roundup(value):
    """Round up to nearest integer (like Excel ROUNDUP(x, 0))."""
    import math
    return Decimal(str(math.ceil(float(value))))


def calculate_payroll(employee, month: int, year: int,
                      present_days: float, total_working_days: int,
                      advance_deduction: float = 0,
                      other_deductions: float = 0,
                      ytd_tds: float = 0,
                      config=None):
    """
    Full payroll calculation for one employee. Returns dict for SalaryRecord.
    """
    if config is None:
        from flask import current_app
        config = current_app.config

    ratio = _d(present_days) / _d(total_working_days) if total_working_days else _d(1)

    # ── Earned earnings (prorated) ────────────────────────────────────────────
    basic = _round2(_d(employee.basic_salary) * ratio)
    hra = _round2(_d(employee.hra) * ratio)
    da = _round2(_d(employee.da) * ratio)
    special = _round2(_d(employee.special_allowance) * ratio)
    other_allow = _round2(_d(employee.other_allowance) * ratio)
    petrol = _round2(_d(employee.petrol_allowance) * ratio)
    conveyance = _round2(_d(employee.conveyance) * ratio)
    medical = _round2(_d(employee.medical_allowance) * ratio)

    # PF wage base = earned gross EXCLUDING petrol allowance
    pf_wage_base = basic + hra + da + special + other_allow + conveyance + medical
    gross_earned = pf_wage_base + petrol

    # ── PF ───────────────────────────────────────────────────────────────────
    pf_employee = _d(0)
    pf_employer_epf = _d(0)
    pf_employer_eps = _d(0)
    pf_employer_edli = _d(0)
    pf_employer_total = _d(0)

    if employee.pf_applicable:
        pf_ceiling = _d(config.get('PF_WAGE_CEILING', 15000))
        # Cap PF base at ₹15,000 if ceiling applies; directors may have no ceiling
        pf_base = pf_wage_base
        if getattr(employee, 'pf_on_ceiling', True):
            pf_base = min(pf_wage_base, pf_ceiling)

        pf_employee = _round2(pf_base * _d('0.12'))
        pf_employer_epf = _round2(pf_base * _d('0.0367'))

        eps_base = min(pf_base, pf_ceiling)
        pf_employer_eps_raw = eps_base * _d('0.0833')
        eps_max = _d(config.get('EPS_MAX', 1250))
        pf_employer_eps = _round2(min(pf_employer_eps_raw, eps_max))

        pf_employer_edli = _round2(pf_base * _d('0.005'))
        pf_employer_total = pf_employer_epf + pf_employer_eps + pf_employer_edli

    # ── ESIC ─────────────────────────────────────────────────────────────────
    esic_employee = _d(0)
    esic_employer = _d(0)
    esic_ceiling = _d(config.get('ESIC_CEILING', 21000))

    if employee.esic_applicable and _d(employee.gross_salary) <= esic_ceiling:
        esic_employee = _roundup(gross_earned * _d('0.0075'))
        esic_employer = _roundup(gross_earned * _d('0.0325'))

    # ── Professional Tax (Gujarat) ────────────────────────────────────────────
    # ₹200/month if monthly gross ≥ ₹12,000; prorated gross may be lower on LOP
    pt = _d(0)
    if getattr(employee, 'pt_applicable', True):
        if gross_earned >= _d(12000):
            pt = _d(200)

    # ── Gujarat LWF ───────────────────────────────────────────────────────────
    lwf_employee = _d(0)
    lwf_employer = _d(0)
    lwf_months = config.get('LWF_MONTHS', [6, 12])
    if month in lwf_months:
        lwf_employee = _d(config.get('LWF_EMPLOYEE', 6))
        lwf_employer = _d(config.get('LWF_EMPLOYER', 12))

    # ── Gratuity (employer liability, not deducted) ───────────────────────────
    gratuity = _round2(basic * _d('0.0481'))

    # ── Statutory Bonus ───────────────────────────────────────────────────────
    # 8.33% of basic (capped at ₹3,500/month per Payment of Bonus Act)
    bonus_base = min(basic, _d(3500))
    bonus = _round2(bonus_base * _d('0.0833'))

    # ── TDS ───────────────────────────────────────────────────────────────────
    tds = _round2(_d(calculate_monthly_tds(
        employee=employee,
        month=month,
        year=year,
        gross_earned=float(gross_earned),
        pf_employee=float(pf_employee),
        ytd_tds=ytd_tds,
        config=config,
    )))

    # ── Totals ────────────────────────────────────────────────────────────────
    advance_ded = _round2(_d(advance_deduction))
    other_ded = _round2(_d(other_deductions))
    total_deductions = (pf_employee + esic_employee + pt + lwf_employee +
                        tds + advance_ded + other_ded)
    net_salary = _round2(gross_earned - total_deductions)

    # CTC = gross_earned + all employer contributions
    ctc = _round2(gross_earned + pf_employer_total + esic_employer + lwf_employer + gratuity)

    return {
        'month': month,
        'year': year,
        'total_working_days': total_working_days,
        'present_days': present_days,
        'lop_days': float(total_working_days) - float(present_days),
        'basic': basic,
        'hra': hra,
        'da': da,
        'special_allowance': special,
        'other_allowance': other_allow,
        'petrol_allowance': petrol,
        'conveyance': conveyance,
        'medical_allowance': medical,
        'pf_wage_base': pf_wage_base,
        'gross_earned': gross_earned,
        'pf_employee': pf_employee,
        'pf_employer_epf': pf_employer_epf,
        'pf_employer_eps': pf_employer_eps,
        'pf_employer_edli': pf_employer_edli,
        'pf_employer_total': pf_employer_total,
        'esic_employee': esic_employee,
        'esic_employer': esic_employer,
        'pt': pt,
        'lwf_employee': lwf_employee,
        'lwf_employer': lwf_employer,
        'gratuity': gratuity,
        'bonus': bonus,
        'tds': tds,
        'advance_deduction': advance_ded,
        'other_deductions': other_ded,
        'total_deductions': total_deductions,
        'net_salary': net_salary,
        'ctc': ctc,
    }


def calculate_monthly_tds(employee, month: int, year: int,
                           gross_earned: float, pf_employee: float,
                           ytd_tds: float = 0, config=None):
    """
    Monthly TDS using projected annual income method.
    Spreads remaining tax across remaining months of the financial year.
    """
    fy_start_month = 4
    if month >= fy_start_month:
        months_elapsed = month - fy_start_month + 1
    else:
        months_elapsed = month + (12 - fy_start_month) + 1

    remaining_months = 12 - months_elapsed + 1
    if remaining_months <= 0:
        remaining_months = 1

    annual_gross = gross_earned * 12
    regime = getattr(employee, 'tds_regime', 'new') or 'new'
    annual_tax = _compute_annual_tax(annual_gross, pf_employee * 12, regime)

    remaining_tax = max(0, annual_tax - ytd_tds)
    return round(remaining_tax / remaining_months, 2)


def _compute_annual_tax(annual_gross: float, annual_pf: float, regime: str) -> float:
    if regime == 'old':
        return _old_regime_tax(annual_gross, annual_pf)
    return _new_regime_tax(annual_gross)


def _new_regime_tax(annual_gross: float) -> float:
    """New tax regime FY 2024-25 — standard deduction ₹75,000."""
    taxable = max(0, annual_gross - 75000)
    if taxable <= 300000:
        return 0
    # Rebate u/s 87A — no tax if taxable ≤ ₹7,00,000
    if taxable <= 700000:
        return 0
    tax = 0
    slabs = [
        (300000, 0.00),
        (400000, 0.05),
        (300000, 0.10),
        (200000, 0.15),
        (300000, 0.20),
    ]
    remaining = taxable
    for slab_limit, rate in slabs:
        if remaining <= 0:
            break
        in_slab = min(remaining, slab_limit)
        tax += in_slab * rate
        remaining -= in_slab
    if remaining > 0:
        tax += remaining * 0.30
    return round(tax * 1.04, 2)  # + 4% cess


def _old_regime_tax(annual_gross: float, annual_pf: float) -> float:
    """Old tax regime FY 2024-25 — standard deduction ₹50,000."""
    taxable = max(0, annual_gross - 50000 - annual_pf)
    if taxable <= 250000:
        return 0
    if taxable <= 500000:
        return 0  # Rebate u/s 87A
    tax = 0
    slabs = [
        (250000, 0.00),
        (250000, 0.05),
        (500000, 0.20),
    ]
    remaining = taxable
    for slab_limit, rate in slabs:
        if remaining <= 0:
            break
        in_slab = min(remaining, slab_limit)
        tax += in_slab * rate
        remaining -= in_slab
    if remaining > 0:
        tax += remaining * 0.30
    return round(tax * 1.04, 2)
