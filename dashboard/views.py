from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
import json
import csv
import pandas as pd
from io import BytesIO
import xlsxwriter

from accounts.models import User, TeacherProfile, StudentProfile
from courses.models import Course, CourseEnrollment, Review
from classes.models import ClassSession, TeacherAvailability
from payments.models import Payment
from .models import DashboardWidget, Announcement, ActivityLog
from .utils import get_dashboard_stats, get_chart_data, log_activity

@login_required
def dashboard_home(request):
    """Main dashboard view - redirects based on user type"""
    if request.user.is_teacher:
        return redirect('dashboard:teacher_dashboard')
    elif request.user.is_student:
        return redirect('dashboard:student_dashboard')
    elif request.user.is_admin:
        return redirect('dashboard:admin_dashboard')
    else:
        return redirect('dashboard:default_dashboard')


@login_required
def default_dashboard(request):
    """Default dashboard for users without specific roles"""
    context = {
        'user': request.user,
        'announcements': Announcement.objects.filter(
            is_active=True,
            start_date__lte=timezone.now()
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
        )[:5],
    }
    return render(request, 'dashboard/home.html', context)


# ============== STUDENT DASHBOARD ==============

@login_required
def student_dashboard(request):
    """Student dashboard view"""
    if not request.user.is_student:
        messages.error(request, _('Access denied. Students only.'))
        return redirect('dashboard:home')
    
    # Get student data
    enrollments = CourseEnrollment.objects.filter(
        student=request.user,
        status='active'
    ).select_related('course', 'teacher')
    
    upcoming_sessions = ClassSession.objects.filter(
        student=request.user,
        date__gte=timezone.now().date(),
        status='scheduled'
    ).order_by('date', 'start_time')[:5]
    
    recent_sessions = ClassSession.objects.filter(
        student=request.user,
        status='completed'
    ).order_by('-date')[:5]
    
    # Calculate statistics
    total_courses = enrollments.count()
    completed_courses = CourseEnrollment.objects.filter(
        student=request.user,
        status='completed'
    ).count()
    
    total_classes = ClassSession.objects.filter(
        student=request.user
    ).count()
    
    attended_classes = ClassSession.objects.filter(
        student=request.user,
        status='completed'
    ).count()
    
    # Calculate average progress
    avg_progress = enrollments.aggregate(
        avg=Avg('progress_percentage')
    )['avg'] or 0
    
    # Get announcements
    announcements = []
    for announcement in Announcement.objects.filter(is_active=True):
        if announcement.is_visible_to(request.user):
            announcements.append(announcement)
    
    # Recent activity
    recent_activity = ActivityLog.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]
    
    context = {
        'enrollments': enrollments,
        'upcoming_sessions': upcoming_sessions,
        'recent_sessions': recent_sessions,
        'total_courses': total_courses,
        'completed_courses': completed_courses,
        'total_classes': total_classes,
        'attended_classes': attended_classes,
        'avg_progress': round(avg_progress, 1),
        'announcements': announcements[:3],
        'recent_activity': recent_activity,
        'attendance_rate': round((attended_classes / total_classes * 100) if total_classes > 0 else 0, 1),
    }
    
    # Log activity
    log_activity(request.user, 'dashboard_view', {'type': 'student'})
    
    return render(request, 'dashboard/student/dashboard.html', context)


@login_required
def student_courses(request):
    """Student's enrolled courses"""
    if not request.user.is_student:
        messages.error(request, _('Access denied. Students only.'))
        return redirect('dashboard:home')
    
    enrollments = CourseEnrollment.objects.filter(
        student=request.user
    ).select_related('course', 'teacher').order_by('-enrolled_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    context = {
        'enrollments': enrollments,
        'status_filter': status_filter,
    }
    
    return render(request, 'dashboard/student/my_courses.html', context)


@login_required
def student_schedule(request):
    """Student's class schedule"""
    if not request.user.is_student:
        messages.error(request, _('Access denied. Students only.'))
        return redirect('dashboard:home')
    
    # Get date range
    date_from = request.GET.get('from', timezone.now().date())
    date_to = request.GET.get('to', timezone.now().date() + timedelta(days=30))
    
    sessions = ClassSession.objects.filter(
        student=request.user,
        date__range=[date_from, date_to]
    ).select_related('course', 'teacher').order_by('date', 'start_time')
    
    # Group sessions by date for calendar view
    sessions_by_date = {}
    for session in sessions:
        date_key = session.date.strftime('%Y-%m-%d')
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append({
            'id': str(session.session_id),
            'title': session.course.title,
            'time': session.start_time.strftime('%H:%M'),
            'teacher': session.teacher.get_full_name(),
            'status': session.status,
            'platform': session.platform,
            'meeting_link': session.meeting_link,
        })
    
    context = {
        'sessions': sessions,
        'sessions_json': json.dumps(sessions_by_date),
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'dashboard/student/schedule.html', context)


@login_required
def student_progress(request):
    """Student's learning progress"""
    if not request.user.is_student:
        messages.error(request, _('Access denied. Students only.'))
        return redirect('dashboard:home')
    
    enrollments = CourseEnrollment.objects.filter(
        student=request.user,
        status__in=['active', 'completed']
    ).select_related('course')
    
    progress_data = []
    for enrollment in enrollments:
        total_lessons = len(enrollment.course.get_syllabus_sections())
        completed_lessons = len(enrollment.completed_lessons)
        
        progress_data.append({
            'course': enrollment.course,
            'enrollment': enrollment,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': enrollment.progress_percentage,
            'status': enrollment.status,
            'started_at': enrollment.started_at,
            'last_activity': ClassSession.objects.filter(
                student=request.user,
                course=enrollment.course,
                status='completed'
            ).order_by('-date').first()
        })
    
    # Calculate overall statistics
    total_enrolled = enrollments.count()
    total_completed = enrollments.filter(status='completed').count()
    avg_progress = enrollments.aggregate(Avg('progress_percentage'))['progress_percentage__avg'] or 0
    
    # Learning streak
    streak = calculate_learning_streak(request.user)
    
    context = {
        'progress_data': progress_data,
        'total_enrolled': total_enrolled,
        'total_completed': total_completed,
        'avg_progress': round(avg_progress, 1),
        'learning_streak': streak,
    }
    
    return render(request, 'dashboard/student/progress.html', context)


@login_required
def student_payments(request):
    """Student's payment history"""
    if not request.user.is_student:
        messages.error(request, _('Access denied. Students only.'))
        return redirect('dashboard:home')
    
    payments = Payment.objects.filter(
        user=request.user
    ).select_related('course').order_by('-created_at')
    
    # Calculate totals
    total_paid = payments.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    pending_payments = payments.filter(status='pending').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    context = {
        'payments': payments,
        'total_paid': total_paid,
        'pending_payments': pending_payments,
    }
    
    return render(request, 'dashboard/student/payments.html', context)


# ============== TEACHER DASHBOARD ==============

@login_required
def teacher_dashboard(request):
    """Teacher dashboard view"""
    if not request.user.is_teacher:
        messages.error(request, _('Access denied. Teachers only.'))
        return redirect('dashboard:home')
    
    # Get teacher data
    teacher_profile = request.user.teacher_profile
    
    # Upcoming sessions
    upcoming_sessions = ClassSession.objects.filter(
        teacher=request.user,
        date__gte=timezone.now().date(),
        status='scheduled'
    ).select_related('course', 'student').order_by('date', 'start_time')[:5]
    
    # Active students
    active_students = CourseEnrollment.objects.filter(
        teacher=request.user,
        status='active'
    ).select_related('student', 'course').values('student').distinct().count()
    
    # This month's statistics
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_sessions = ClassSession.objects.filter(
        teacher=request.user,
        date__gte=current_month_start.date(),
        status='completed'
    ).count()
    
    # Calculate earnings
    monthly_earnings = calculate_teacher_earnings(request.user, current_month_start)
    
    # Recent reviews
    recent_reviews = Review.objects.filter(
        teacher=request.user
    ).select_related('student', 'course').order_by('-created_at')[:5]
    
    # Student distribution by course
    student_distribution = CourseEnrollment.objects.filter(
        teacher=request.user,
        status='active'
    ).values('course__title').annotate(count=Count('student'))
    
    # Today's schedule
    today_sessions = ClassSession.objects.filter(
        teacher=request.user,
        date=timezone.now().date()
    ).select_related('course', 'student').order_by('start_time')
    
    # Announcements
    announcements = []
    for announcement in Announcement.objects.filter(is_active=True):
        if announcement.is_visible_to(request.user):
            announcements.append(announcement)
    
    context = {
        'teacher_profile': teacher_profile,
        'upcoming_sessions': upcoming_sessions,
        'active_students': active_students,
        'monthly_sessions': monthly_sessions,
        'monthly_earnings': monthly_earnings,
        'recent_reviews': recent_reviews,
        'student_distribution': student_distribution,
        'today_sessions': today_sessions,
        'announcements': announcements[:3],
        'rating': teacher_profile.rating,
        'total_reviews': teacher_profile.total_reviews,
    }
    
    # Log activity
    log_activity(request.user, 'dashboard_view', {'type': 'teacher'})
    
    return render(request, 'dashboard/teacher/dashboard.html', context)


@login_required
def teacher_students(request):
    """Teacher's students list"""
    if not request.user.is_teacher:
        messages.error(request, _('Access denied. Teachers only.'))
        return redirect('dashboard:home')
    
    # Get all students enrolled in teacher's courses
    enrollments = CourseEnrollment.objects.filter(
        teacher=request.user
    ).select_related('student', 'course', 'student__student_profile')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        enrollments = enrollments.filter(status=status_filter)
    
    # Filter by course
    course_filter = request.GET.get('course')
    if course_filter:
        enrollments = enrollments.filter(course__id=course_filter)
    
    # Get unique courses for filter dropdown
    teacher_courses = Course.objects.filter(
        teachers=request.user
    ).distinct()
    
    # Group students
    students_data = {}
    for enrollment in enrollments:
        student_id = enrollment.student.id
        if student_id not in students_data:
            students_data[student_id] = {
                'student': enrollment.student,
                'enrollments': [],
                'total_classes': 0,
                'attended_classes': 0,
                'last_session': None,
            }
        
        students_data[student_id]['enrollments'].append(enrollment)
        
        # Calculate attendance
        sessions = ClassSession.objects.filter(
            teacher=request.user,
            student=enrollment.student,
            course=enrollment.course
        )
        students_data[student_id]['total_classes'] += sessions.count()
        students_data[student_id]['attended_classes'] += sessions.filter(
            status='completed'
        ).count()
        
        # Get last session
        last_session = sessions.order_by('-date').first()
        if last_session:
            if not students_data[student_id]['last_session'] or \
               last_session.date > students_data[student_id]['last_session'].date:
                students_data[student_id]['last_session'] = last_session
    
    context = {
        'students_data': students_data.values(),
        'teacher_courses': teacher_courses,
        'status_filter': status_filter,
        'course_filter': course_filter,
    }
    
    return render(request, 'dashboard/teacher/my_students.html', context)


@login_required
def teacher_schedule(request):
    """Teacher's class schedule and availability"""
    if not request.user.is_teacher:
        messages.error(request, _('Access denied. Teachers only.'))
        return redirect('dashboard:home')
    
    # Get date range
    date_from = request.GET.get('from', timezone.now().date())
    date_to = request.GET.get('to', timezone.now().date() + timedelta(days=30))
    
    # Get sessions
    sessions = ClassSession.objects.filter(
        teacher=request.user,
        date__range=[date_from, date_to]
    ).select_related('course', 'student').order_by('date', 'start_time')
    
    # Get availability
    availability = TeacherAvailability.objects.filter(
        teacher=request.user,
        is_active=True
    ).order_by('day_of_week', 'start_time')
    
    # Group sessions by date for calendar
    sessions_by_date = {}
    for session in sessions:
        date_key = session.date.strftime('%Y-%m-%d')
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        sessions_by_date[date_key].append({
            'id': str(session.session_id),
            'title': f"{session.course.title} - {session.student.get_full_name()}",
            'time': f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}",
            'status': session.status,
            'platform': session.platform,
        })
    
    context = {
        'sessions': sessions,
        'availability': availability,
        'sessions_json': json.dumps(sessions_by_date),
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'dashboard/teacher/schedule.html', context)


@login_required
def teacher_earnings(request):
    """Teacher's earnings and financial reports"""
    if not request.user.is_teacher:
        messages.error(request, _('Access denied. Teachers only.'))
        return redirect('dashboard:home')
    
    # Get date range
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    
    if not date_from:
        date_from = timezone.now().replace(day=1)
    else:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
    
    if not date_to:
        date_to = timezone.now()
    else:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
    
    # Calculate earnings
    payments = Payment.objects.filter(
        course__teachers=request.user,
        status='completed',
        paid_at__range=[date_from, date_to]
    ).select_related('course', 'user')
    
    # Commission rate (teacher gets 80%)
    commission_rate = 0.8
    
    earnings_data = []
    total_earnings = 0
    
    for payment in payments:
        teacher_earning = float(payment.amount) * commission_rate
        earnings_data.append({
            'payment': payment,
            'gross_amount': payment.amount,
            'commission': float(payment.amount) * (1 - commission_rate),
            'net_amount': teacher_earning,
        })
        total_earnings += teacher_earning
    
    # Monthly breakdown
    monthly_breakdown = {}
    for payment in payments:
        month_key = payment.paid_at.strftime('%Y-%m')
        if month_key not in monthly_breakdown:
            monthly_breakdown[month_key] = {
                'month': payment.paid_at.strftime('%B %Y'),
                'total': 0,
                'count': 0,
            }
        monthly_breakdown[month_key]['total'] += float(payment.amount) * commission_rate
        monthly_breakdown[month_key]['count'] += 1
    
    # Sessions taught
    sessions_taught = ClassSession.objects.filter(
        teacher=request.user,
        date__range=[date_from.date(), date_to.date()],
        status='completed'
    ).count()
    
    context = {
        'earnings_data': earnings_data,
        'total_earnings': total_earnings,
        'monthly_breakdown': monthly_breakdown.values(),
        'sessions_taught': sessions_taught,
        'date_from': date_from.date(),
        'date_to': date_to.date(),
        'commission_rate': commission_rate * 100,
    }
    
    return render(request, 'dashboard/teacher/earnings.html', context)


@login_required
def teacher_availability(request):
    """Manage teacher availability"""
    if not request.user.is_teacher:
        messages.error(request, _('Access denied. Teachers only.'))
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        # Handle availability update
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        action = request.POST.get('action')
        
        if action == 'add':
            TeacherAvailability.objects.create(
                teacher=request.user,
                day_of_week=int(day),
                start_time=start_time,
                end_time=end_time,
                is_active=True
            )
            messages.success(request, _('Availability slot added successfully.'))
        elif action == 'delete':
            slot_id = request.POST.get('slot_id')
            TeacherAvailability.objects.filter(
                id=slot_id,
                teacher=request.user
            ).delete()
            messages.success(request, _('Availability slot removed.'))
        
        return redirect('dashboard:teacher_availability')
    
    # Get current availability
    availability = TeacherAvailability.objects.filter(
        teacher=request.user
    ).order_by('day_of_week', 'start_time')
    
    # Group by day
    availability_by_day = {}
    for slot in availability:
        day = slot.day_of_week
        if day not in availability_by_day:
            availability_by_day[day] = []
        availability_by_day[day].append(slot)
    
    context = {
        'availability': availability,
        'availability_by_day': availability_by_day,
        'days_of_week': TeacherAvailability.DAYS_OF_WEEK,
    }
    
    return render(request, 'dashboard/teacher/availability.html', context)


# ============== ADMIN DASHBOARD ==============

@login_required
def admin_analytics(request):
    """Admin analytics dashboard with detailed statistics"""
    if not request.user.is_admin:
        return redirect('dashboard:default_dashboard')
    
    # Basic statistics
    total_students = User.objects.filter(is_student=True).count()
    total_teachers = User.objects.filter(is_teacher=True).count()
    total_courses = Course.objects.count()
    total_revenue = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Course enrollment statistics
    popular_courses = Course.objects.annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-enrollment_count')[:5]
    
    # Payment statistics
    recent_payments = Payment.objects.select_related('user', 'course').order_by('-created_at')[:10]
    
    # Teacher performance
    top_teachers = User.objects.filter(is_teacher=True).annotate(
        total_earnings=Sum('payments_received__amount', filter=Q(payments_received__status='completed')),
        total_students=Count('courses_taught__enrollments', distinct=True),
        avg_rating=Avg('reviews_received__rating')
    ).order_by('-total_earnings')[:5]
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_revenue': total_revenue,
        'popular_courses': popular_courses,
        'recent_payments': recent_payments,
        'top_teachers': top_teachers,
    }
    
    # Add chart data if needed
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'data': {
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_courses': total_courses,
                'total_revenue': float(total_revenue) if total_revenue else 0,
            }
        })
    
    return render(request, 'dashboard/admin/analytics.html', context)

@login_required
def admin_dashboard(request):
    """Admin dashboard view"""
    if not request.user.is_admin:
        messages.error(request, _('Access denied. Admins only.'))
        return redirect('dashboard:home')
    
    # Get statistics
    total_users = User.objects.count()
    total_students = User.objects.filter(user_type='student').count()
    total_teachers = User.objects.filter(user_type='teacher').count()
    total_courses = Course.objects.filter(is_active=True).count()
    
    # Recent registrations
    recent_users = User.objects.order_by('-created_at')[:10]
    
    # Revenue statistics
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_revenue = Payment.objects.filter(
        status='completed',
        paid_at__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_revenue = Payment.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Active sessions today
    today_sessions = ClassSession.objects.filter(
        date=timezone.now().date()
    ).count()
    
    # Pending assessments
    from classes.models import Assessment
    pending_assessments = Assessment.objects.filter(
        status='submitted'
    ).count()
    
    # Course statistics
    course_stats = CourseEnrollment.objects.values(
        'course__title'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Platform statistics
    platform_stats = ClassSession.objects.values(
        'platform'
    ).annotate(
        count=Count('id')
    )
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'recent_users': recent_users,
        'monthly_revenue': monthly_revenue,
        'total_revenue': total_revenue,
        'today_sessions': today_sessions,
        'pending_assessments': pending_assessments,
        'course_stats': course_stats,
        'platform_stats': platform_stats,
    }
    
    return render(request, 'dashboard/admin/dashboard.html', context)


@login_required
def admin_reports(request):
    """Generate and download reports"""
    if not request.user.is_admin:
        messages.error(request, _('Access denied. Admins only.'))
        return redirect('dashboard:home')
    
    report_type = request.GET.get('type')
    format_type = request.GET.get('format', 'csv')
    date_from = request.GET.get('from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('to', timezone.now().strftime('%Y-%m-%d'))
    
    if report_type == 'users':
        return generate_users_report(format_type, date_from, date_to)
    elif report_type == 'payments':
        return generate_payments_report(format_type, date_from, date_to)
    elif report_type == 'sessions':
        return generate_sessions_report(format_type, date_from, date_to)
    elif report_type == 'enrollments':
        return generate_enrollments_report(format_type, date_from, date_to)
    
    # Show report selection page
    context = {
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'dashboard/admin/reports.html', context)

# ============== UTILITY FUNCTIONS ==============

def calculate_teacher_earnings(teacher, start_date):
    """Calculate teacher earnings for a period"""
    from payments.models import Payment
    
    payments = Payment.objects.filter(
        course__teachers=teacher,
        status='completed',
        paid_at__gte=start_date
    )
    
    total = sum(float(p.amount) for p in payments)
    commission_rate = 0.8  # Teacher gets 80%
    
    return total * commission_rate


def calculate_learning_streak(user):
    """Calculate user's learning streak in days"""
    sessions = ClassSession.objects.filter(
        student=user,
        status='completed'
    ).order_by('-date').values_list('date', flat=True)
    
    if not sessions:
        return 0
    
    streak = 1
    last_date = sessions[0]
    
    for date in sessions[1:]:
        if (last_date - date).days == 1:
            streak += 1
            last_date = date
        else:
            break
    
    return streak


def generate_users_report(format_type, date_from, date_to):
    """Generate users report"""
    users = User.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).select_related('student_profile', 'teacher_profile')
    
    data = []
    for user in users:
        data.append({
            'ID': user.id,
            'Email': user.email,
            'Name': user.get_full_name(),
            'Type': user.user_type,
            'Phone': user.phone_number,
            'Country': user.country,
            'Registered': user.created_at.strftime('%Y-%m-%d %H:%M'),
            'Verified Email': user.is_email_verified,
            'Verified Phone': user.is_phone_verified,
        })
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="users_report_{date_from}_{date_to}.csv"'
        
        writer = csv.DictWriter(response, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)
        
        return response
    
    elif format_type == 'excel':
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Users')
        
        # Write headers
        if data:
            headers = list(data[0].keys())
            for col, header in enumerate(headers):
                worksheet.write(0, col, header)
            
            # Write data
            for row_num, row_data in enumerate(data, 1):
                for col, value in enumerate(row_data.values()):
                    worksheet.write(row_num, col, str(value))
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="users_report_{date_from}_{date_to}.xlsx"'
        
        return response


def generate_payments_report(format_type, date_from, date_to):
    """Generate payments report"""
    payments = Payment.objects.filter(
        created_at__date__range=[date_from, date_to]
    ).select_related('user', 'course')
    
    data = []
    for payment in payments:
        data.append({
            'Transaction ID': str(payment.transaction_id),
            'User': payment.user.email,
            'Course': payment.course.title if payment.course else 'N/A',
            'Amount': float(payment.amount),
            'Currency': payment.currency,
            'Method': payment.payment_method,
            'Status': payment.status,
            'Date': payment.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payments_report_{date_from}_{date_to}.csv"'
        
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return response
    
    # Excel format similar to users report
    # ... (implement similar to generate_users_report)


def generate_sessions_report(format_type, date_from, date_to):
    """Generate class sessions report"""
    sessions = ClassSession.objects.filter(
        date__range=[date_from, date_to]
    ).select_related('course', 'teacher', 'student')
    
    data = []
    for session in sessions:
        data.append({
            'Session ID': str(session.session_id),
            'Date': session.date.strftime('%Y-%m-%d'),
            'Time': f"{session.start_time} - {session.end_time}",
            'Course': session.course.title,
            'Teacher': session.teacher.get_full_name(),
            'Student': session.student.get_full_name(),
            'Platform': session.platform,
            'Status': session.status,
            'Duration': session.duration_minutes,
        })
    
    # Generate CSV or Excel based on format_type
    # ... (implement similar to above)


def generate_enrollments_report(format_type, date_from, date_to):
    """Generate course enrollments report"""
    enrollments = CourseEnrollment.objects.filter(
        enrolled_at__date__range=[date_from, date_to]
    ).select_related('course', 'student', 'teacher')
    
    data = []
    for enrollment in enrollments:
        data.append({
            'Student': enrollment.student.email,
            'Course': enrollment.course.title,
            'Teacher': enrollment.teacher.get_full_name() if enrollment.teacher else 'N/A',
            'Status': enrollment.status,
            'Progress': f"{enrollment.progress_percentage}%",
            'Enrolled': enrollment.enrolled_at.strftime('%Y-%m-%d'),
            'Started': enrollment.started_at.strftime('%Y-%m-%d') if enrollment.started_at else 'N/A',
        })
    
    # Generate CSV or Excel based on format_type
    # ... (implement similar to above)