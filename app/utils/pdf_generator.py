"""PDF payslip generator using ReportLab — matches client salary sheet structure."""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io
import calendar as _cal

PRIMARY    = colors.HexColor('#1a56db')
DARK_BLUE  = colors.HexColor('#1e3a8a')
LIGHT_BLUE = colors.HexColor('#dbeafe')
LIGHT_GREEN= colors.HexColor('#dcfce7')
LIGHT_RED  = colors.HexColor('#fee2e2')
LIGHT_ORG  = colors.HexColor('#fef3c7')
LIGHT_GRAY = colors.HexColor('#f3f4f6')
DARK       = colors.HexColor('#111827')
MUTED      = colors.HexColor('#6b7280')
GREEN      = colors.HexColor('#166534')
RED        = colors.HexColor('#991b1b')
ORANGE     = colors.HexColor('#92400e')


def _inr(value):
    try:
        v = float(value or 0)
        return f'₹{v:,.2f}'
    except (TypeError, ValueError):
        return '₹0.00'


def _p(text, size=9, bold=False, color=DARK, align=TA_LEFT):
    style = ParagraphStyle('ps', fontSize=size,
                           fontName='Helvetica-Bold' if bold else 'Helvetica',
                           textColor=color, alignment=align)
    return Paragraph(str(text), style)


def generate_payslip_pdf(record, config) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    emp = record.employee
    company = config.get('COMPANY_NAME', 'Company')
    company_addr = config.get('COMPANY_ADDRESS', '')

    # ── Header ──────────────────────────────────────────────────────────────
    hdr = ParagraphStyle('hdr', fontSize=16, fontName='Helvetica-Bold',
                         textColor=PRIMARY, alignment=TA_CENTER)
    sub = ParagraphStyle('sub', fontSize=9, textColor=MUTED, alignment=TA_CENTER)
    story.append(Paragraph(company, hdr))
    story.append(Paragraph(company_addr, sub))
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f'SALARY SLIP — {_cal.month_name[record.month].upper()} {record.year}',
        ParagraphStyle('title', fontSize=12, fontName='Helvetica-Bold',
                       textColor=PRIMARY, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 4*mm))

    # ── Employee info grid ───────────────────────────────────────────────────
    def lbl(t): return Paragraph(t, ParagraphStyle('l', fontSize=8, textColor=MUTED, fontName='Helvetica-Bold'))
    def val(t): return Paragraph(str(t or '—'), ParagraphStyle('v', fontSize=8, textColor=DARK))

    info = [
        [lbl('Employee Code'), val(emp.emp_code), lbl('Department'), val(emp.department)],
        [lbl('Employee Name'), val(emp.full_name), lbl('Designation'), val(emp.designation)],
        [lbl('Gender'), val(getattr(emp, 'gender', '—')), lbl('Location'), val(getattr(emp, 'location', '—'))],
        [lbl('Date of Joining'), val(emp.date_of_joining), lbl('PAN Number'), val(emp.pan_number)],
        [lbl('UAN (PF)'), val(emp.uan_number), lbl('ESIC IP No.'), val(emp.esic_ip_number)],
        [lbl('Bank Account'), val(emp.bank_account), lbl('Bank Name'), val(emp.bank_name)],
        [lbl('Month Days'), val(record.total_working_days), lbl('Present Days'), val(record.present_days)],
        [lbl('LOP Days'), val(record.lop_days), lbl('TDS Regime'), val((emp.tds_regime or 'new').upper())],
    ]
    info_tbl = Table(info, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
    info_tbl.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Earnings & Deductions ────────────────────────────────────────────────
    def hdr_p(t, c=colors.white):
        return Paragraph(t, ParagraphStyle('h', fontSize=8, fontName='Helvetica-Bold',
                                           textColor=c, alignment=TA_LEFT))

    earn_head = [[hdr_p('EARNINGS'), hdr_p('Amount'), hdr_p('DEDUCTIONS'), hdr_p('Amount')]]

    earn_rows = [
        ('Basic Salary',      record.basic),
        ('HRA',               record.hra),
        ('Dearness Allow.',   record.da),
        ('Special Allow.',    record.special_allowance),
        ('Other Allow.',      record.other_allowance),
        ('Petrol Allow.',     record.petrol_allowance),
        ('Conveyance',        record.conveyance),
        ('Medical Allow.',    record.medical_allowance),
    ]
    ded_rows = [
        ('PF (Emp 12%)',      record.pf_employee),
        ('ESIC (Emp 0.75%)', record.esic_employee),
        ('Prof. Tax (PT)',    record.pt),
        ('Gujarat LWF',      record.lwf_employee),
        ('TDS',              record.tds),
        ('Advance Recovery', record.advance_deduction),
        ('Other Deductions', record.other_deductions),
        ('', ''),
    ]
    max_r = max(len(earn_rows), len(ded_rows))
    earn_rows += [('', '')] * (max_r - len(earn_rows))
    ded_rows += [('', '')] * (max_r - len(ded_rows))

    table_data = earn_head[:]
    for i in range(max_r):
        el, ev = earn_rows[i]
        dl, dv = ded_rows[i]
        table_data.append([
            el, _inr(ev) if ev != '' else '',
            dl, _inr(dv) if dv != '' else '',
        ])
    table_data.append(['Gross Earned', _inr(record.gross_earned),
                       'Total Deductions', _inr(record.total_deductions)])

    sal_tbl = Table(table_data, colWidths=[5.5*cm, 3*cm, 5.5*cm, 3*cm])
    sal_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, LIGHT_GRAY]),
        ('BACKGROUND', (0, -1), (-1, -1), LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(sal_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Net Pay box ──────────────────────────────────────────────────────────
    net_tbl = Table([[Paragraph(
        f'NET PAY: {_inr(record.net_salary)}',
        ParagraphStyle('net', fontSize=13, fontName='Helvetica-Bold',
                       textColor=PRIMARY, alignment=TA_CENTER)
    )]], colWidths=[17*cm])
    net_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BOX', (0, 0), (-1, -1), 1.5, PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(net_tbl)
    story.append(Spacer(1, 6*mm))

    story.append(HRFlowable(width='100%', thickness=0.5, color=MUTED))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'This is a computer-generated payslip and does not require a signature.',
        ParagraphStyle('footer', fontSize=7, textColor=MUTED, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()
