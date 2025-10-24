from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from openpyxl import Workbook

def render_salary_pdf(slip):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 2*cm
    p.setFont("Helvetica-Bold", 16)
    p.drawString(2*cm, y, "Salary Slip"); y -= 1.2*cm
    p.setFont("Helvetica", 11)

    lines = [
        f"Employee: {slip.employee.code} - {slip.employee.first_name} {slip.employee.last_name}",
        f"Department: {slip.employee.department} | Designation: {slip.employee.designation}",
        f"Month: {slip.month.strftime('%B %Y')}",
        "", "Earnings:",
        f"  Basic       : ₹ {slip.basic}",
        f"  HRA (20%)   : ₹ {slip.hra}",
        f"  Allowances  : ₹ {slip.allowances}",
        "", "Deductions:",
        f"  Total       : ₹ {slip.deductions}",
        "", f"Net Pay: ₹ {slip.net_pay}",
    ]
    for line in lines:
        p.drawString(2*cm, y, line)
        y -= 0.8*cm

    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()

    resp = HttpResponse(pdf, content_type='application/pdf')
    filename = f"salary_slip_{slip.employee.code}_{slip.month.strftime('%Y_%m')}.pdf"
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp

def export_payroll_excel(slips):
    wb = Workbook()
    ws = wb.active
    ws.title = "Payroll"
    ws.append(["Code","Name","Month","Basic","HRA","Allowances","Deductions","Net Pay"])
    for s in slips:
        ws.append([
            s.employee.code,
            f"{s.employee.first_name} {s.employee.last_name}".strip(),
            s.month.strftime("%Y-%m"),
            float(s.basic), float(s.hra), float(s.allowances), float(s.deductions), float(s.net_pay)
        ])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)

    resp = HttpResponse(bio.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp['Content-Disposition'] = 'attachment; filename="payroll.xlsx"'
    return resp
