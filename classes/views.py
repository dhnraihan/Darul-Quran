from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import json
import uuid

from .models import ClassSession, TeacherAvailability, Assessment
from courses.models import Course, CourseEnrollment
from .forms import AssessmentForm, ClassSessionForm
from .tasks import send_assessment_notification, send_class_reminder

User = get_user_model()

@login_required
def class_schedule(request):
    """View class schedule"""
    if request.user.is_teacher:
        sessions = ClassSession.objects.filter(teacher=request.user)
    else:
        sessions = ClassSession.objects.filter(student=request.user)
    
    # Filter by date range
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    course_filter = request.GET.get('course')
    status_filter = request.GET.get('status')
    
    if date_from:
        sessions = sessions.filter(date__gte=date_from)
    if date_to:
        sessions = sessions.filter(date__lte=date_to)
    if course_filter:
        sessions = sessions.filter(course__id=course_filter)
    if status_filter:
        sessions = sessions.filter(status=status_filter)
    
    sessions = sessions.select_related('course', 'teacher', 'student').order_by('date', 'start_time')
    
    # Group sessions by date for calendar view
    sessions_by_date = {}
    for session in sessions:
        date_key = session.date.strftime('%Y-%m-%d')
        if date_key not in sessions_by_date:
            sessions_by_date[date_key] = []
        
        sessions_by_date[date_key].append({
            'id': str(session.session_id),
            'title': session.course.title,
            'time': f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}",
            'teacher': session.teacher.get_full_name(),
            'student': session.student.get_full_name(),
            'status': session.status,
            'platform': session.platform,
            'meeting_link': session.meeting_link,
        })
    
    # Get user's courses for filter
    if request.user.is_teacher:
        user_courses = Course.objects.filter(teachers=request.user)
    else:
        user_courses = Course.objects.filter(
            enrollments__student=request.user
        ).distinct()
    
    context = {
        'sessions': sessions,
        'sessions_json': json.dumps(sessions_by_date),
        'is_teacher': request.user.is_teacher,
        'user_courses': user_courses,
        'date_from': date_from,
        'date_to': date_to,
        'today': timezone.now().date(),
    }
    return render(request, 'classes/schedule.html', context)


def calendar_view(request):
    """Calendar view of classes"""
    return render(request, 'classes/calendar.html')


@login_required
def class_detail(request, session_id):
    """Class session detail view"""
    session = get_object_or_404(
        ClassSession.objects.select_related('course', 'teacher', 'student'),
        session_id=session_id
    )
    
    # Check permission
    if request.user != session.teacher and request.user != session.student:
        messages.error(request, _('You do not have permission to view this session.'))
        return redirect('classes:schedule')
    
    # Handle session updates
    if request.method == 'POST' and request.user == session.teacher:
        action = request.POST.get('action')
        
        if action == 'update_notes':
            session.teacher_notes = request.POST.get('teacher_notes', '')
            session.save()
            messages.success(request, _('Notes updated successfully!'))
        else:
            form = ClassSessionForm(request.POST, instance=session)
            if form.is_valid():
                form.save()
                messages.success(request, _('Session updated successfully!'))
        
        return redirect('classes:session_detail', session_id=session.session_id)
    
    # Calculate time until session
    session_datetime = timezone.make_aware(
        datetime.combine(session.date, session.start_time)
    )
    time_until = session_datetime - timezone.now()
    
    context = {
        'session': session,
        'is_teacher': request.user == session.teacher,
        'whatsapp_link': session.get_whatsapp_link(),
        'time_until': time_until,
        'tomorrow': timezone.now().date() + timedelta(days=1),
    }
    return render(request, 'classes/session_detail.html', context)


def assessment_form(request):
    """Multi-step assessment form"""
    courses = Course.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # Handle both regular form submission and AJAX
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            assessment = Assessment.objects.create(
                full_name=data.get('full_name'),
                phone_number=data.get('phone_number'),
                email=data.get('email', ''),
                preferred_course_id=data.get('preferred_course'),
                trial_date=data.get('trial_date'),
                trial_time=data.get('trial_time'),
                current_level=data.get('current_level', ''),
                age=data.get('age'),
                notes=data.get('notes', ''),
                status='submitted'
            )
            
            # Send notifications
            send_assessment_notification.delay(assessment.id)
            
            return JsonResponse({'success': True})
        else:
            form = AssessmentForm(request.POST)
            if form.is_valid():
                assessment = form.save(commit=False)
                assessment.status = 'submitted'
                assessment.save()
                
                # Send notifications
                send_assessment_notification.delay(assessment.id)
                
                messages.success(
                    request,
                    _('Thank you for your submission! We will contact you soon.')
                )
                return redirect('home')
    else:
        form = AssessmentForm()
    
    context = {
        'form': form,
        'courses': courses,
    }
    return render(request, 'classes/assessment_form.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def submit_assessment(request):
    """Submit assessment form via AJAX"""
    try:
        data = json.loads(request.body)
        
        assessment = Assessment.objects.create(
            full_name=data.get('full_name'),
            phone_number=data.get('phone_number'),
            email=data.get('email', ''),
            preferred_course_id=data.get('preferred_course') if data.get('preferred_course') else None,
            trial_date=data.get('trial_date') if data.get('trial_date') else None,
            trial_time=data.get('trial_time') if data.get('trial_time') else None,
            current_level=data.get('current_level', ''),
            age=data.get('age') if data.get('age') else None,
            notes=data.get('notes', ''),
            status='submitted'
        )
        
        # Send notifications
        send_assessment_notification.delay(assessment.id)
        
        return JsonResponse({'success': True, 'message': 'Assessment submitted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def teacher_availability(request):
    """Manage teacher availability"""
    if not request.user.is_teacher:
        messages.error(request, _('Only teachers can manage availability.'))
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            TeacherAvailability.objects.create(
                teacher=request.user,
                day_of_week=int(request.POST.get('day')),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                is_active=True
            )
            messages.success(request, _('Availability added successfully.'))
        
        elif action == 'delete':
            slot_id = request.POST.get('slot_id')
            TeacherAvailability.objects.filter(
                id=slot_id,
                teacher=request.user
            ).delete()
            messages.success(request, _('Availability removed.'))
        
        return redirect('classes:availability')
    
    availability = TeacherAvailability.objects.filter(
        teacher=request.user
    ).order_by('day_of_week', 'start_time')
    
    context = {
        'availability': availability,
        'days_of_week': TeacherAvailability.DAYS_OF_WEEK,
    }
    return render(request, 'classes/teacher_availability.html', context)


@login_required
@require_http_methods(["GET"])
def get_teacher_availability(request, teacher_id):
    """API endpoint to get teacher's available slots"""
    teacher = get_object_or_404(User, id=teacher_id, user_type='teacher')
    date = request.GET.get('date')
    
    if not date:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        day_of_week = date_obj.weekday()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Get teacher's availability for this day
    availabilities = TeacherAvailability.objects.filter(
        teacher=teacher,
        day_of_week=day_of_week,
        is_active=True
    )
    
    # Get existing sessions for this date
    existing_sessions = ClassSession.objects.filter(
        teacher=teacher,
        date=date_obj,
        status__in=['scheduled', 'in_progress']
    ).values_list('start_time', 'end_time')
    
    available_slots = []
    for availability in availabilities:
        # Generate 30-minute slots
        current_time = availability.start_time
        while current_time < availability.end_time:
            end_time = (
                datetime.combine(date_obj, current_time) + 
                timedelta(minutes=30)
            ).time()
            
            # Check if slot is not already booked
            is_available = True
            for session_start, session_end in existing_sessions:
                if (current_time >= session_start and current_time < session_end) or \
                   (end_time > session_start and end_time <= session_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    'start': current_time.strftime('%H:%M'),
                    'end': end_time.strftime('%H:%M'),
                })
            
            current_time = end_time
    
    return JsonResponse({'slots': available_slots})


@login_required
def book_class(request):
    """Book a new class session"""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        teacher_id = request.POST.get('teacher_id')
        date = request.POST.get('date')
        time = request.POST.get('time')
        platform = request.POST.get('platform', 'teams')
        notes = request.POST.get('notes', '')
        
        try:
            course = Course.objects.get(id=course_id)
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            
            # Check enrollment
            enrollment = CourseEnrollment.objects.filter(
                student=request.user,
                course=course
            ).first()
            
            if not enrollment:
                messages.error(request, _('You must be enrolled in the course to book a class.'))
                return redirect('courses:enroll', slug=course.slug)
            
            # Create session
            session_date = datetime.strptime(date, '%Y-%m-%d').date()
            session_time = datetime.strptime(time, '%H:%M').time()
            end_time = (datetime.combine(session_date, session_time) + timedelta(minutes=course.session_duration_minutes)).time()
            
            session = ClassSession.objects.create(
                course=course,
                teacher=teacher,
                student=request.user,
                date=session_date,
                start_time=session_time,
                end_time=end_time,
                duration_minutes=course.session_duration_minutes,
                platform=platform,
                status='scheduled',
                student_notes=notes
            )
            
            # Send confirmation
            send_class_reminder.delay(session.id)
            
            messages.success(request, _('Class booked successfully!'))
            return redirect('classes:session_detail', session_id=session.session_id)
            
        except (Course.DoesNotExist, User.DoesNotExist):
            messages.error(request, _('Invalid course or teacher.'))
            return redirect('classes:book')
    
    # GET request
    courses = Course.objects.filter(
        enrollments__student=request.user,
        enrollments__status='active'
    ).distinct()
    
    context = {
        'courses': courses,
    }
    return render(request, 'classes/book_class.html', context)


@login_required
def confirm_booking(request):
    """Confirm class booking"""
    if request.method == 'POST':
        # Process booking confirmation
        session_data = request.session.get('booking_data')
        if not session_data:
            messages.error(request, _('No booking data found.'))
            return redirect('classes:book')
        
        # Create the session
        # ... booking logic ...
        
        messages.success(request, _('Booking confirmed!'))
        return redirect('classes:schedule')
    
    return render(request, 'classes/confirm_booking.html')


@login_required
def reschedule_session(request, session_id):
    """Reschedule a class session"""
    session = get_object_or_404(ClassSession, session_id=session_id)
    
    # Check permission
    if request.user != session.teacher and request.user != session.student:
        messages.error(request, _('You cannot reschedule this session.'))
        return redirect('classes:schedule')
    
    if request.method == 'POST':
        new_date = request.POST.get('date')
        new_time = request.POST.get('time')
        reason = request.POST.get('reason', '')
        notify_other = request.POST.get('notify_other') == 'on'
        
        try:
            old_date = session.date
            old_time = session.start_time
            
            session.date = datetime.strptime(new_date, '%Y-%m-%d').date()
            session.start_time = datetime.strptime(new_time, '%H:%M').time()
            session.end_time = (
                datetime.combine(session.date, session.start_time) + 
                timedelta(minutes=session.duration_minutes)
            ).time()
            session.status = 'scheduled'  # Reset to scheduled
            session.save()
            
            # Log the reschedule
            if request.user == session.teacher:
                session.teacher_notes = f"Rescheduled from {old_date} {old_time}. Reason: {reason}\n{session.teacher_notes}"
            else:
                session.student_notes = f"Rescheduled from {old_date} {old_time}. Reason: {reason}\n{session.student_notes}"
            session.save()
            
            # Send notification to other party
            if notify_other:
                send_class_reminder.delay(session.id)
            
            messages.success(request, _('Session rescheduled successfully!'))
            return redirect('classes:session_detail', session_id=session.session_id)
            
        except ValueError:
            messages.error(request, _('Invalid date or time format.'))
    
    # Get teacher availability for the reschedule form
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    context = {
        'session': session,
        'tomorrow': tomorrow.strftime('%Y-%m-%d'),
    }
    return render(request, 'classes/reschedule.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_session(request, session_id):
    """Cancel a class session"""
    session = get_object_or_404(ClassSession, session_id=session_id)
    
    # Check permission
    if request.user != session.teacher and request.user != session.student:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    session.status = 'cancelled'
    session.save()
    
    # Send notification
    send_class_reminder.delay(session.id)
    
    messages.success(request, _('Session cancelled.'))
    return redirect('classes:schedule')


@login_required
@require_http_methods(["POST"])
def complete_session(request, session_id):
    """Mark session as complete"""
    session = get_object_or_404(ClassSession, session_id=session_id)
    
    # Only teacher can mark as complete
    if request.user != session.teacher:
        return JsonResponse({'success': False, 'error': 'Only teacher can mark as complete'}, status=403)
    
    session.status = 'completed'
    session.attendance_marked = True
    session.save()
    
    # Update student progress
    enrollment = CourseEnrollment.objects.filter(
        student=session.student,
        course=session.course
    ).first()
    
    if enrollment:
        # Update progress
        completed_lessons = enrollment.completed_lessons or []
        lesson_id = f"session_{session.id}"
        if lesson_id not in completed_lessons:
            completed_lessons.append(lesson_id)
            enrollment.completed_lessons = completed_lessons
            enrollment.save()
    
    messages.success(request, _('Session marked as complete.'))
    return redirect('classes:session_detail', session_id=session.session_id)


# ============== API ENDPOINTS ==============

'''

@login_required
@require_http_methods(["GET"])
def api_sessions_list(request):
    """API endpoint to get list of sessions"""
    if request.user.is_teacher:
        sessions = ClassSession.objects.filter(teacher=request.user)
    else:
        sessions = ClassSession.objects.filter(student=request.user)
    
    # Apply filters
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')
    status = request.GET.get('status')
    
    if date_from:
        sessions = sessions.filter(date__gte=date_from)
    if date_to:
        sessions = sessions.filter(date__lte=date_to)
    if status:
        sessions = sessions.filter(status=status)
    
    sessions = sessions.order_by('date', 'start_time')[:50]
    
    data = []
    for session in sessions:
        data.append({
            'id': str(session.session_id),
            'course': session.course.title,
            'date': session.date.isoformat(),
            'start_time': session.start_time.strftime('%H:%M'),
            'end_time': session.end_time.strftime('%H:%M'),
            'teacher': session.teacher.get_full_name(),
            'student': session.student.get_full_name(),
            'platform': session.platform,
            'status': session.status,
            'meeting_link': session.meeting_link,
        })
    
    return JsonResponse({'success': True, 'sessions': data})


@login_required
@require_http_methods(["GET"])
def api_session_detail(request, session_id):
    """API endpoint to get session details"""
    try:
        session = ClassSession.objects.get(session_id=session_id)
    except ClassSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)
    
    # Check permission
    if request.user != session.teacher and request.user != session.student:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    data = {
        'id': str(session.session_id),
        'course': session.course.title,
        'date': session.date.isoformat(),
        'time': f"{session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M')}",
        'teacher': session.teacher.get_full_name(),
        'student': session.student.get_full_name(),
        'platform': session.get_platform_display(),
        'status': session.get_status_display(),
        'topic': session.topic,
        'meeting_link': session.meeting_link,
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def api_teacher_availability(request, teacher_id):
    """API endpoint for teacher availability"""
    return get_teacher_availability(request, teacher_id)


@login_required
@require_http_methods(["POST"])
def api_book_session(request):
    """API endpoint to book a session"""
    data = json.loads(request.body)
    
    course_id = data.get('course_id')
    teacher_id = data.get('teacher_id')
    date = data.get('date')
    time = data.get('time')
    
    try:
        course = Course.objects.get(id=course_id)
        teacher = User.objects.get(id=teacher_id, user_type='teacher')
        
        session = ClassSession.objects.create(
            course=course,
            teacher=teacher,
            student=request.user,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            start_time=datetime.strptime(time, '%H:%M').time(),
            end_time=(datetime.strptime(time, '%H:%M') + timedelta(minutes=course.session_duration_minutes)).time(),
            duration_minutes=course.session_duration_minutes,
            platform=data.get('platform', 'teams'),
            status='scheduled'
        )
        
        return JsonResponse({
            'success': True,
            'session_id': str(session.session_id),
            'message': 'Session booked successfully'
        })
        
    except (Course.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)


@login_required
@require_http_methods(["POST"])
def api_reschedule(request):
    """API endpoint to reschedule a session"""
    data = json.loads(request.body)
    session_id = data.get('session_id')
    new_date = data.get('date')
    new_time = data.get('time')
    
    try:
        session = ClassSession.objects.get(session_id=session_id)
        
        # Check permission
        if request.user != session.teacher and request.user != session.student:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        session.date = datetime.strptime(new_date, '%Y-%m-%d').date()
        session.start_time = datetime.strptime(new_time, '%H:%M').time()
        session.save()
        
        return JsonResponse({'success': True, 'message': 'Session rescheduled'})
        
    except ClassSession.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'}, status=404)


'''