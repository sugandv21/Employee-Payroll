from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import EmployeeForm, AttendanceForm
from .models import Employee, Attendance, SalarySlip
from .utils import render_salary_pdf, export_payroll_excel


# ---------- Home ----------
def home(request):
    context = {
        "emp_count": Employee.objects.count(),
        "att_count": Attendance.objects.count(),
        "slip_count": SalarySlip.objects.count(),
    }
    return render(request, 'payroll/layout/home.html', context)


# ---------- Employees ----------

class StaffOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only admin can access that page.")
        return redirect('payroll:home')


# Make list visible to any logged-in user (staff or employee).
class EmployeeList(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'payroll/layout/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 10


# Keep create/update/delete staff-only
class EmployeeCreate(LoginRequiredMixin, StaffOnlyMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/layout/employee_form.html'
    success_url = reverse_lazy('payroll:employee_list')


class EmployeeUpdate(LoginRequiredMixin, StaffOnlyMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'payroll/layout/employee_form.html'
    success_url = reverse_lazy('payroll:employee_list')


class EmployeeDelete(LoginRequiredMixin, StaffOnlyMixin, DeleteView):
    model = Employee
    template_name = 'payroll/layout/employee_confirm_delete.html'
    success_url = reverse_lazy('payroll:employee_list')


# ---------- Attendance ----------

@login_required
def attendance_list(request):
    """
    Staff: see all (+ optional date filter).
    Employee (non-staff): see only own records.
    """
    qs = Attendance.objects.select_related('employee').order_by('-date')

    if request.user.is_staff:
        sel = request.GET.get('date')
        if sel:
            try:
                dt = datetime.strptime(sel, '%Y-%m-%d').date()
                qs = qs.filter(date=dt)
            except ValueError:
                messages.error(request, "Invalid date filter.")
    else:
        # Non-staff employees: restrict to their own attendance only
        try:
            me = request.user.employee
        except Employee.DoesNotExist:
            messages.error(request, "Your login isn’t linked to an employee profile. Contact admin.")
            return redirect('payroll:home')
        qs = qs.filter(employee=me)

    return render(request, 'payroll/layout/attendance_list.html', {'records': qs})


@login_required
@user_passes_test(lambda u: u.is_staff)
def attendance_create(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Attendance saved.")
                return redirect('payroll:attendance_list')
            except Exception as e:
                messages.error(request, f"Could not save attendance: {e}")
    else:
        form = AttendanceForm()
    return render(request, 'payroll/layout/attendance_form.html', {'form': form})


# ---------- Payroll (Mixed: STAFF can see all, EMPLOYEE sees only own) ----------

@login_required
def salary_generate(request):
    """
    - STAFF: can pick any employee and month; see all slips.
    - EMPLOYEE (non-staff): can generate and see only their own.
    """
    if request.user.is_staff:
        employees = Employee.objects.filter(is_active=True).order_by('code')
        slips = SalarySlip.objects.select_related('employee').order_by('-month', 'employee__code')
    else:
        # Ensure user is linked to an employee profile
        try:
            me = request.user.employee
        except Employee.DoesNotExist:
            messages.error(request, "Your login is not linked to an employee profile. Contact admin.")
            return redirect('payroll:home')
        employees = Employee.objects.filter(pk=me.pk, is_active=True)
        slips = SalarySlip.objects.select_related('employee').filter(employee__user=request.user).order_by('-month')

    if request.method == 'POST':
        if request.user.is_staff:
            emp_id = request.POST.get('employee')
            month_str = request.POST.get('month')  # format yyyy-mm
            if not (emp_id and month_str):
                messages.error(request, "Select employee and month.")
                return redirect('payroll:salary_generate')
            employee = get_object_or_404(Employee, pk=emp_id, is_active=True)
        else:
            month_str = request.POST.get('month')
            if not month_str:
                messages.error(request, "Select month.")
                return redirect('payroll:salary_generate')
            employee = request.user.employee

        try:
            # Save month as first day (YYYY-MM-01)
            month_date = datetime.strptime(month_str + '-01', '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid month.")
            return redirect('payroll:salary_generate')

        data = SalarySlip.compute_for_month(employee, month_date)
        slip, created = SalarySlip.objects.get_or_create(
            employee=employee,
            month=data['first_day'],
            defaults={
                'basic': data['basic'],
                'hra': data['hra'],
                'allowances': data['allowances'],
                'deductions': data['deductions'],
                'net_pay': data['net_pay'],
            }
        )
        if not created:
            # Update if regenerating
            slip.basic = data['basic']
            slip.hra = data['hra']
            slip.allowances = data['allowances']
            slip.deductions = data['deductions']
            slip.net_pay = data['net_pay']
            slip.save()

        messages.success(request, f"Salary slip ready for {employee.code} - {slip.month:%b %Y}.")
        return redirect('payroll:salary_detail', pk=slip.pk)

    return render(request, 'payroll/layout/salary_generate.html', {
        'employees': employees,
        'slips': slips
    })


@login_required
def salary_detail(request, pk):
    slip = get_object_or_404(SalarySlip.objects.select_related('employee'), pk=pk)
    # Employee can only view their own slip
    if (not request.user.is_staff) and (slip.employee.user_id != request.user.id):
        raise Http404()
    return render(request, 'payroll/layout/salary_detail.html', {'slip': slip})


@login_required
def salary_pdf(request, pk):
    slip = get_object_or_404(SalarySlip, pk=pk)
    if (not request.user.is_staff) and (slip.employee.user_id != request.user.id):
        raise Http404()
    return render_salary_pdf(slip)


@login_required
def salary_export_excel(request):
    if request.user.is_staff:
        slips = SalarySlip.objects.select_related('employee').order_by('-month', 'employee__code')
    else:
        slips = SalarySlip.objects.select_related('employee').filter(employee__user=request.user).order_by('-month')
    return export_payroll_excel(slips)
