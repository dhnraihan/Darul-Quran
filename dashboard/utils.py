from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from datetime import datetime, timedelta
from accounts.models import User
from courses.models import CourseEnrollment
from classes.models import ClassSession
from payments.models import Payment
from .models import ActivityLog

def get_dashboard_stats(user):
    """Get dashboard statistics based on user type"""
    stats = {}
    
    if user.is_student:
        stats = get_student_stats(user)
    elif user.is_teacher:
        stats = get_teacher_stats(user)
    elif user.is_admin:
        stats = get_admin_stats()
    
    return stats


def get_student_stats(user):
    """Get statistics for student dashboard"""
    enrollments = CourseEnrollment.objects.filter(student=user)
    sessions = ClassSession.objects.filter(student=user)
    
    return {
        'total_courses': enrollments.count(),
        'active_courses': enrollments.filter(status='active').count(),
        'completed_courses': enrollments.filter(status='completed').count(),
        'total_sessions': sessions.count(),
        'attended_sessions': sessions.filter(status='completed').count(),
        'upcoming_sessions': sessions.filter(
            date__gte=timezone.now().date(),
            status='scheduled'
        ).count(),
        'avg_progress': enrollments.filter(
            status='active'
        ).aggregate(Avg('progress_percentage'))['progress_percentage__avg'] or 0,
    }


def get_teacher_stats(user):
    """Get statistics for teacher dashboard"""
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    enrollments = CourseEnrollment.objects.filter(teacher=user)
    sessions = ClassSession.objects.filter(teacher=user)
    
    return {
        'active_students': enrollments.filter(status='active').values('student').distinct().count(),
        'total_sessions': sessions.count(),
        'monthly_sessions': sessions.filter(date__gte=current_month_start.date()).count(),
        'upcoming_sessions': sessions.filter(
            date__gte=timezone.now().date(),
            status='scheduled'
        ).count(),
        'completion_rate': calculate_completion_rate(user),
    }


def get_admin_stats():
    """Get statistics for admin dashboard"""
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    return {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(user_type='student').count(),
        'total_teachers': User.objects.filter(user_type='teacher').count(),
        'new_users_this_month': User.objects.filter(created_at__gte=current_month_start).count(),
        'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
        'monthly_revenue': Payment.objects.filter(
            status='completed',
            paid_at__gte=current_month_start
        ).aggregate(Sum('amount'))['amount__sum'] or 0,
    }


def calculate_completion_rate(teacher):
    """Calculate class completion rate for teacher"""
    total = ClassSession.objects.filter(
        teacher=teacher,
        date__lt=timezone.now().date()
    ).count()
    
    completed = ClassSession.objects.filter(
        teacher=teacher,
        date__lt=timezone.now().date(),
        status='completed'
    ).count()
    
    if total > 0:
        return round((completed / total) * 100, 1)
    return 0


def log_activity(user, action, details=None, request=None):
    """Log user activity"""
    activity = ActivityLog(
        user=user,
        action=action,
        details=details or {}
    )
    
    if request:
        activity.ip_address = get_client_ip(request)
        activity.user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    activity.save()
    return activity


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_chart_data(user, chart_type):
    """Get data for dashboard charts"""
    if chart_type == 'progress':
        return get_progress_chart_data(user)
    elif chart_type == 'attendance':
        return get_attendance_chart_data(user)
    elif chart_type == 'earnings':
        return get_earnings_chart_data(user)
    elif chart_type == 'enrollment':
        return get_enrollment_chart_data()
    
    return {}


def get_progress_chart_data(user):
    """Get course progress data for charts"""
    if user.is_student:
        enrollments = CourseEnrollment.objects.filter(
            student=user,
            status='active'
        ).select_related('course')
        
        return {
            'labels': [e.course.title for e in enrollments],
            'data': [float(e.progress_percentage) for e in enrollments],
        }
    return {}


def get_attendance_chart_data(user):
    """Get attendance data for charts"""
    # Last 7 days attendance
    dates = []
    attendance = []
    
    for i in range(6, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        dates.append(date.strftime('%b %d'))
        
        if user.is_student:
            count = ClassSession.objects.filter(
                student=user,
                date=date,
                status='completed'
            ).count()
        else:
            count = ClassSession.objects.filter(
                teacher=user,
                date=date,
                status='completed'
            ).count()
        
        attendance.append(count)
    
    return {
        'labels': dates,
        'data': attendance,
    }


def get_earnings_chart_data(user):
    """Get earnings data for teacher"""
    if not user.is_teacher:
        return {}
    
    # Last 6 months earnings
    months = []
    earnings = []
    
    for i in range(5, -1, -1):
        date = timezone.now() - timedelta(days=30*i)
        month_start = date.replace(day=1)
        
        if i == 0:
            month_end = timezone.now()
        else:
            next_month = month_start + timedelta(days=32)
            month_end = next_month.replace(day=1) - timedelta(days=1)
        
        months.append(month_start.strftime('%b'))
        
        total = Payment.objects.filter(
            course__teachers=user,
            status='completed',
            paid_at__range=[month_start, month_end]
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        earnings.append(float(total) * 0.8)  # 80% commission
    
    return {
        'labels': months,
        'data': earnings,
    }


def get_enrollment_chart_data():
    """Get enrollment trends for admin"""
    # Last 30 days enrollments
    dates = []
    enrollments = []
    
    for i in range(29, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        dates.append(date.strftime('%m/%d'))
        
        count = CourseEnrollment.objects.filter(
            enrolled_at__date=date
        ).count()
        
        enrollments.append(count)
    
    return {
        'labels': dates,
        'data': enrollments,
    }