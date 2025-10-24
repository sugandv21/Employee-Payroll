from django.contrib import admin
from .models import Employee, Attendance, SalarySlip


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('code', 'first_name', 'last_name', 'department', 'designation', 'base_salary', 'is_active', 'user')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('code', 'first_name', 'last_name', 'email', 'phone', 'department', 'designation', 'user__username')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'working_hours')
    list_filter = ('status', 'date', 'employee__department')
    search_fields = ('employee__code', 'employee__first_name', 'employee__last_name')


@admin.register(SalarySlip)
class SalarySlipAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'basic', 'hra', 'allowances', 'deductions', 'net_pay', 'generated_at')
    list_filter = ('month', 'employee__department')
    search_fields = ('employee__code', 'employee__first_name', 'employee__last_name')
