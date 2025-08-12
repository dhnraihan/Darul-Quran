from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard_home, name='home'),
    path('default/', views.default_dashboard, name='default_dashboard'),
    
    # Student Dashboard
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/progress/', views.student_progress, name='student_progress'),
    path('student/payments/', views.student_payments, name='student_payments'),
    
    # Teacher Dashboard
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/schedule/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher/earnings/', views.teacher_earnings, name='teacher_earnings'),
    path('teacher/availability/', views.teacher_availability, name='teacher_availability'),
    
    # Admin Dashboard
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    
    # API endpoints
    # path('api/stats/', views.api_dashboard_stats, name='api_stats'),
    # path('api/chart-data/', views.api_chart_data, name='api_chart_data'),
]