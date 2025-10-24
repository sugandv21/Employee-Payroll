from decimal import Decimal
from calendar import monthrange
from django.conf import settings
from django.db import models
from django.utils import timezone


class Employee(models.Model):
    # Link to Django auth user for employee self-service login (optional)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link this employee to a login user (non-staff)."
    )
    code = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    join_date = models.DateField(default=timezone.now)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return f"{self.code} - {full}" if full else self.code


class Attendance(models.Model):
    STATUS_CHOICES = [('P', 'Present'), ('A', 'Absent'), ('L', 'Leave')]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('8.00'))

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.code} {self.date} {self.status}"


class SalarySlip(models.Model):
    """
    One slip per employee per month (month saved as first day of that month).
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField(help_text="Store as first day of month (YYYY-MM-01)")
    basic = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'month')
        ordering = ['-month', 'employee__code']

    def __str__(self):
        m = self.month.strftime("%b %Y")
        return f"Slip {self.employee.code} - {m}"

    @staticmethod
    def compute_for_month(employee, any_date_in_month):
        """
        Net = Base + HRA(20%) + Allowances(10%) - (AbsentDays × Base/DaysInMonth)
        """
        first_day = any_date_in_month.replace(day=1)
        _, days_in_month = monthrange(first_day.year, first_day.month)
        month_end = first_day.replace(day=days_in_month)

        base = Decimal(employee.base_salary or 0)
        hra = (base * Decimal('0.20')).quantize(Decimal('0.01'))
        allowances = (base * Decimal('0.10')).quantize(Decimal('0.01'))

        absents = Attendance.objects.filter(
            employee=employee,
            date__gte=first_day,
            date__lte=month_end,
            status='A'
        ).count()

        per_day = (base / Decimal(days_in_month)).quantize(Decimal('0.01')) if days_in_month else Decimal('0.00')
        absent_deduction = (per_day * Decimal(absents)).quantize(Decimal('0.01'))

        deductions = absent_deduction
        gross = base + hra + allowances
        net = (gross - deductions).quantize(Decimal('0.01'))

        return {
            'first_day': first_day,
            'basic': base,
            'hra': hra,
            'allowances': allowances,
            'deductions': deductions,
            'net_pay': net,
        }
