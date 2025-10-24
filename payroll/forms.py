
# payroll/forms.py
from django import forms
from .models import Employee, Attendance

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'code','first_name','last_name','email','phone',
            'department','designation','join_date','base_salary','is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class':'form-control'}),
            'first_name': forms.TextInput(attrs={'class':'form-control'}),
            'last_name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'}),
            'department': forms.TextInput(attrs={'class':'form-control'}),
            'designation': forms.TextInput(attrs={'class':'form-control'}),
            'join_date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'base_salary': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee','date','status','working_hours']
        widgets = {
            'employee': forms.Select(attrs={'class':'form-select'}),
            'date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'status': forms.Select(attrs={'class':'form-select'}),
            'working_hours': forms.NumberInput(attrs={'class':'form-control','step':'0.25'}),
        }
