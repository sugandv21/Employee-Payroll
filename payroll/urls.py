from django.urls import path
from . import views

app_name = 'payroll'

urlpatterns = [
    path('', views.home, name='home'),

    # Employees
    path('employees/', views.EmployeeList.as_view(), name='employee_list'),
    path('employees/add/', views.EmployeeCreate.as_view(), name='employee_add'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdate.as_view(), name='employee_edit'),
    path('employees/<int:pk>/delete/', views.EmployeeDelete.as_view(), name='employee_delete'),

    # Attendance
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/add/', views.attendance_create, name='attendance_add'),

    # Payroll
    path('salary/', views.salary_generate, name='salary_generate'),
    path('salary/<int:pk>/', views.salary_detail, name='salary_detail'),
    path('salary/<int:pk>/pdf/', views.salary_pdf, name='salary_pdf'),
    path('salary/export/excel/', views.salary_export_excel, name='salary_export_excel'),
]
