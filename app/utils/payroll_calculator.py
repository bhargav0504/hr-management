"""
Indian payroll calculation engine — Gujarat norms.

PF     : Employee 12% of pf_wage_base (excl. petrol, capped ₹15,000)
         Employer: EPF 3.67% + EPS 8.33% (capped ₹1,250; zero if age ≥ 58) + EDLI 0.5%
         All EPFO amounts rounded UP to nearest rupee (ECR filing standard).
ESIC   : Employee 0.75% | Employer 3.25% of esic_wage_base (gross excl. petrol)
         Applicable only if esic_wage_base ≤ ceiling (₹21,000)
PT     : Gujarat — ₹200/month if gross_earned ≥ ₹12,000
LWF    : Gujarat — ₹6 employee / ₹12 employer — June & December only
Gratuity: 4.81% of basic (employer liability)
Bonus  : 8.33% of basic (statutory bonus, capped at ₹3,500 base)
CTC    : gross_earned + employer PF + employer ESIC + LWF employer + gratuity
TDS    : Projected annual income method, new or old regime (FY 2024-25)
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from datetime import date as _date
import calendar as _cal


def _d(value):
    return Decimal(str(value or 0))


def _round2(value):
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _roundup(value):
    """Round up to nearest integer — standard for EPFO ECR challan."""
    return Decimal(str(math.ceil(float(value))))


def _employee_age(employee, year, month):
    """Age in years at the first day of the payroll month."""
    dob = getattr(employee, 'date_of_birth', None)
    if not dob:
        return 0
    ref = _date(year, month, 1)
    return (ref - dob).days // 365


def calculate_payroll(employee, month: int, year: int,
                      present_days: float, total_working_days: int,
                      advance_deduction: float = 0,
                      other_deductions: float = 0,
                      other_deductions_remarks: str = '',
                      ytd_tds: float = 0,
                      config=None,
                      extra_earnings: dict = None):
    """
    Full payroll calculation for one employee.
    extra_earnings: dict of {label: amount} for performance bonus / incentives added via attendance upload.
    Returns dict for SalaryRecord.
    """
    if config is None:
        from flask import current_app
        config = current_app.config

    extra_earnings = extra_earnings or {}

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

    # Extra earnings from attendance upload (performance bonus / incentives)
    extra_total = _round2(sum((_d(v) for v in extra_earnings.values()), _d(0)))

    # PF wage base = earned gross EXCLUDING petrol (also excluded: extra incentives)
    pf_wage_base = basic + hra + da + special + other_allow + conveyance + medical

    # ESIC wage base = same as PF base (petrol/travel excluded per ESIC Act)
    esic_wage_base = pf_wage_base

    # Gross earned = all components including petrol + extra
    gross_earned = pf_wage_base + petrol + extra_total

    # ── PF ───────────────────────────────────────────────────────────────────
    pf_employee = _d(0)
    pf_employer_epf = _d(0)
    pf_employer_eps = _d(0)
    pf_employer_edli = _d(0)
    pf_employer_total = _d(0)

    if employee.pf_applicable:
        pf_ceiling = _d(config.get('PF_WAGE_CEILING', 15000))
        pf_base = pf_wage_base
        if getattr(employee, 'pf_on_ceiling', True):
            pf_base = min(pf_wage_base, pf_ceiling)

        pf_employee = _roundup(pf_base * _d('0.12'))
        pf_employer_epf = _roundup(pf_base * _d('0.0367'))

        # EPS wages = 0 if employee age ≥ 58 (EPFO circular)
        age = _employee_age(employee, year, month)
        pension_ok = getattr(employee, 'pension_eligible', True) and age < 58
        if pension_ok:
            eps_base = min(pf_base, pf_ceiling)
            eps_max = _d(config.get('EPS_MAX', 1250))
            pf_employer_eps = _roundup(min(eps_base * _d('0.0833'), eps_max))
        else:
            pf_employer_eps = _d(0)

        pf_employer_edli = _roundup(pf_base * _d('0.005'))
        pf_employer_total = pf_employer_epf + pf_employer_eps + pf_employer_edli

    # ── ESIC ─────────────────────────────────────────────────────────────────
    esic_employee = _d(0)
    esic_employer = _d(0)

    # Use company-specific ceiling if available
    company = getattr(employee, 'company', None)
    esic_ceiling = _d(float(company.esic_ceiling) if company and company.esic_ceiling else
                      config.get('ESIC_CEILING', 21000))

    # Eligibility checked against esic_wage_base (actual earned, not defined gross)
    if employee.esic_applicable and esic_wage_base <= esic_ceiling:
        esic_employee = _roundup(esic_wage_base * _d('0.0075'))
        esic_employer = _roundup(esic_wage_base * _d('0.0325'))

    # ── Look up Location for state-specific PT/LWF settings ──────────────────
    loc_obj = None
    emp_location = getattr(employee, 'location', None)
    emp_company_id = getattr(employee, 'company_id', None)
    if emp_location and emp_company_id:
        try:
            from app.models.masters import Location as _Location
            loc_obj = _Location.query.filter_by(
                company_id=emp_company_id, name=emp_location).first()
        except Exception:
            pass

    # ── Professional Tax — use location settings if available ────────────────
    pt = _d(0)
    if getattr(employee, 'pt_applicable', True):
        if loc_obj is not None:
            pt_on = loc_obj.pt_applicable
            pt_threshold = _d(float(loc_obj.pt_threshold or 12000))
            pt_amount_val = _d(float(loc_obj.pt_amount or 200))
        else:
            pt_on = True
            pt_threshold = _d(float(company.pt_threshold) if company and company.pt_threshold else 12000)
            pt_amount_val = _d(float(company.pt_amount) if company and company.pt_amount else 200)
        if pt_on and gross_earned >= pt_threshold:
            pt = pt_amount_val

    # ── LWF — use location settings if available ──────────────────────────────
    lwf_employee = _d(0)
    lwf_employer = _d(0)
    if loc_obj is not None:
        lwf_applicable = loc_obj.lwf_applicable
        lwf_month_list = loc_obj.lwf_month_list
        lwf_emp_amt = _d(float(loc_obj.lwf_employee or 6))
        lwf_er_amt = _d(float(loc_obj.lwf_employer or 12))
    else:
        lwf_applicable = company.lwf_applicable if company else True
        lwf_month_list = config.get('LWF_MONTHS', [6, 12])
        lwf_emp_amt = _d(config.get('LWF_EMPLOYEE', 6))
        lwf_er_amt = _d(config.get('LWF_EMPLOYER', 12))
    if lwf_applicable and month in lwf_month_list:
        lwf_employee = lwf_emp_amt
        lwf_employer = lwf_er_amt

    # ── Gratuity (employer liability) ─────────────────────────────────────────
    gratuity = _round2(basic * _d('0.0481'))

    # ── Statutory Bonus ───────────────────────────────────────────────────────
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
        'other_deductions_remarks': other_deductions_remarks,
        'total_deductions': total_deductions,
        'net_salary': net_salary,
        'ctc': ctc,
    }


def calculate_monthly_tds(employee, month: int, year: int,
                           gross_earned: float, pf_employee: float,
                           ytd_tds: float = 0, config=None):
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
    """New tax regime FY 2025-26 — standard deduction ₹75,000."""
    taxable = max(0, annual_gross - 75000)
    if taxable <= 300000:
        return 0
    if taxable <= 700000:
        return 0  # Rebate u/s 87A
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
    return round(tax * 1.04, 2)


def _old_regime_tax(annual_gross: float, annual_pf: float) -> float:
    """Old tax regime FY 2025-26 — standard deduction ₹50,000."""
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
