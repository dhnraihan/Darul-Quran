from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth import get_user_model
import json

from .models import Course, CourseCategory, CourseEnrollment, Review, CourseVideo
from .forms import ReviewForm, EnrollmentForm

User = get_user_model()

def course_list(request, category_slug=None):
    """List all courses with filtering"""
    courses = Course.objects.filter(is_active=True).select_related('category').prefetch_related('teachers')
    categories = CourseCategory.objects.filter(is_active=True)
    
    # Filtering
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(CourseCategory, slug=category_slug)
        courses = courses.filter(category=selected_category)
    
    course_type = request.GET.get('type')
    age_group = request.GET.get('age')
    search = request.GET.get('q')
    sort = request.GET.get('sort', '-created_at')
    
    if course_type:
        courses = courses.filter(course_type=course_type)
    if age_group:
        courses = courses.filter(age_group__in=[age_group, 'all'])
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(title_bn__icontains=search) |
            Q(description_bn__icontains=search)
        )
    
    # Sorting
    if sort == 'price_low':
        courses = courses.order_by('price')
    elif sort == 'price_high':
        courses = courses.order_by('-price')
    elif sort == 'popular':
        courses = courses.annotate(enrollment_count=Count('enrollments')).order_by('-enrollment_count')
    elif sort == 'rating':
        courses = courses.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:
        courses = courses.order_by(sort)
    
    # Pagination
    paginator = Paginator(courses, 12)
    page = request.GET.get('page')
    courses = paginator.get_page(page)
    
    context = {
        'courses': courses,
        'categories': categories,
        'selected_category': selected_category,
        'selected_type': course_type,
        'selected_age': age_group,
        'search_query': search,
        'sort_by': sort,
    }
    return render(request, 'courses/course_list.html', context)


def course_list_by_category(request, category_slug):
    """List courses by category"""
    return course_list(request, category_slug=category_slug)


def course_detail(request, slug):
    """Course detail view"""
    course = get_object_or_404(
        Course.objects.select_related('category', 'created_by')
        .prefetch_related('teachers', 'teachers__teacher_profile', 'videos'),
        slug=slug,
        is_active=True
    )
    
    reviews = course.reviews.filter(is_approved=True).select_related('student').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check enrollment status
    is_enrolled = False
    enrollment = None
    if request.user.is_authenticated:
        enrollment = CourseEnrollment.objects.filter(
            student=request.user,
            course=course
        ).first()
        is_enrolled = enrollment is not None
    
    # Get free videos for preview
    free_videos = course.videos.filter(is_free=True, is_active=True).order_by('order')[:3]
    
    # Get related courses
    related_courses = Course.objects.filter(
        category=course.category,
        is_active=True
    ).exclude(id=course.id)[:4]
    
    # Calculate rating distribution
    rating_distribution = reviews.values('rating').annotate(count=Count('rating')).order_by('rating')
    rating_counts = {i: 0 for i in range(1, 6)}
    for item in rating_distribution:
        rating_counts[item['rating']] = item['count']
    
    context = {
        'course': course,
        'reviews': reviews[:5],
        'avg_rating': avg_rating,
        'total_reviews': reviews.count(),
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'free_videos': free_videos,
        'syllabus': course.get_syllabus_sections(),
        'related_courses': related_courses,
        'rating_counts': rating_counts,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, slug):
    """Enroll in a course"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    # Check if already enrolled
    existing_enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=course
    ).first()
    
    if existing_enrollment:
        messages.info(request, _('You are already enrolled in this course.'))
        return redirect('courses:detail', slug=course.slug)
    
    if request.method == 'POST':
        # Get selected teacher
        teacher_id = request.POST.get('teacher')
        teacher = None
        if teacher_id:
            teacher = get_object_or_404(User, id=teacher_id, user_type='teacher')
        
        # Get additional data
        notes = request.POST.get('notes', '')
        preferred_days = request.POST.getlist('preferred_days')
        preferred_time = request.POST.get('preferred_time', '')
        agree_terms = request.POST.get('agree_terms')
        
        if not agree_terms:
            messages.error(request, _('Please agree to the terms and conditions.'))
            return redirect('courses:enroll', slug=course.slug)
        
        # Create enrollment
        enrollment = CourseEnrollment.objects.create(
            student=request.user,
            course=course,
            teacher=teacher,
            status='pending',
            notes=notes,
        )
        
        # Store preferences in enrollment notes or separate model
        if preferred_days or preferred_time:
            preferences = {
                'preferred_days': preferred_days,
                'preferred_time': preferred_time,
            }
            enrollment.notes = json.dumps(preferences) if not notes else f"{notes}\n{json.dumps(preferences)}"
            enrollment.save()
        
        messages.success(request, _('Successfully enrolled in the course!'))
        
        # Redirect to payment if course is not free
        if not course.is_free:
            return redirect('payments:checkout', course_id=course.id)
        else:
            enrollment.status = 'active'
            enrollment.started_at = timezone.now()
            enrollment.save()
            
            # Send notification to teacher and student
            from classes.tasks import send_enrollment_notification
            send_enrollment_notification.delay(enrollment.id)
            
            return redirect('dashboard:student_courses')
    
    # GET request - show enrollment form
    context = {
        'course': course,
        'teachers': course.teachers.all().select_related('teacher_profile'),
        'courses': Course.objects.filter(is_active=True)[:10],  # For assessment form
    }
    return render(request, 'courses/enroll.html', context)


@login_required
def add_review(request, slug):
    """Add a review for a course"""
    course = get_object_or_404(Course, slug=slug)
    
    # Check if user is enrolled
    enrollment = get_object_or_404(
        CourseEnrollment,
        student=request.user,
        course=course
    )
    
    # Check if already reviewed
    existing_review = Review.objects.filter(
        course=course,
        student=request.user
    ).first()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.course = course
            review.student = request.user
            review.teacher = enrollment.teacher
            review.is_verified_purchase = True
            review.save()
            
            messages.success(request, _('Thank you for your review!'))
            return redirect('courses:detail', slug=course.slug)
    else:
        form = ReviewForm(instance=existing_review)
    
    context = {
        'course': course,
        'form': form,
        'existing_review': existing_review,
        'enrollment': enrollment,
    }
    return render(request, 'courses/add_review.html', context)


@login_required
def course_content(request, slug):
    """Displays the main content page for a course"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    try:
        enrollment = CourseEnrollment.objects.get(student=request.user, course=course)
    except CourseEnrollment.DoesNotExist:
        messages.error(request, _("You are not enrolled in this course."))
        return redirect('courses:detail', slug=slug)
    
    # Get all videos for the course
    videos = course.videos.filter(is_active=True).order_by('order')
    
    # Get upcoming sessions
    from classes.models import ClassSession
    upcoming_sessions = ClassSession.objects.filter(
        student=request.user,
        course=course,
        date__gte=timezone.now().date(),
        status='scheduled'
    ).order_by('date', 'start_time')[:5]
    
    # Calculate progress
    total_lessons = len(course.get_syllabus_sections())
    completed_lessons = len(enrollment.completed_lessons)
    progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'syllabus': course.get_syllabus_sections(),
        'videos': videos,
        'upcoming_sessions': upcoming_sessions,
        'progress_percentage': progress_percentage,
        'completed_lessons': enrollment.completed_lessons,
    }
    return render(request, 'courses/course_content.html', context)


@login_required
def watch_video(request, slug, video_id):
    """Displays a single course video"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    video = get_object_or_404(course.videos, id=video_id, is_active=True)
    
    is_enrolled = CourseEnrollment.objects.filter(
        student=request.user,
        course=course,
        status='active'
    ).exists()
    
    if not video.is_free and not is_enrolled:
        messages.error(request, _("You must be enrolled to watch this video."))
        return redirect('courses:detail', slug=slug)
    
    # Get all videos for navigation
    all_videos = course.videos.filter(is_active=True).order_by('order')
    
    # Find next and previous videos
    video_list = list(all_videos)
    current_index = video_list.index(video)
    prev_video = video_list[current_index - 1] if current_index > 0 else None
    next_video = video_list[current_index + 1] if current_index < len(video_list) - 1 else None
    
    context = {
        'course': course,
        'video': video,
        'is_enrolled': is_enrolled,
        'all_videos': all_videos,
        'prev_video': prev_video,
        'next_video': next_video,
    }
    return render(request, 'courses/watch_video.html', context)


@login_required
@require_http_methods(["POST"])
def update_progress(request, slug):
    """Updates student progress for a course"""
    course = get_object_or_404(Course, slug=slug)
    
    try:
        enrollment = CourseEnrollment.objects.get(
            student=request.user,
            course=course
        )
    except CourseEnrollment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not enrolled'}, status=403)
    
    data = json.loads(request.body)
    lesson_id = data.get('lesson_id')
    
    if lesson_id:
        completed_lessons = enrollment.completed_lessons or []
        if lesson_id not in completed_lessons:
            completed_lessons.append(lesson_id)
            enrollment.completed_lessons = completed_lessons
            
            # Update progress percentage
            total_lessons = len(course.get_syllabus_sections())
            enrollment.progress_percentage = (len(completed_lessons) / total_lessons * 100) if total_lessons > 0 else 0
            
            # Check if course is completed
            if enrollment.progress_percentage >= 100:
                enrollment.status = 'completed'
                enrollment.completed_at = timezone.now()
            
            enrollment.save()
            
            return JsonResponse({
                'success': True,
                'progress': enrollment.progress_percentage,
                'completed_lessons': completed_lessons,
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)


def teacher_courses(request, teacher_id):
    """Lists all courses taught by a specific teacher"""
    teacher = get_object_or_404(User, id=teacher_id, user_type='teacher')
    courses = Course.objects.filter(
        teachers=teacher,
        is_active=True
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        student_count=Count('enrollments', distinct=True)
    )
    
    # Get teacher statistics
    total_students = CourseEnrollment.objects.filter(
        teacher=teacher,
        status='active'
    ).values('student').distinct().count()
    
    total_reviews = Review.objects.filter(teacher=teacher).count()
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'total_students': total_students,
        'total_reviews': total_reviews,
    }
    return render(request, 'courses/teacher_courses.html', context)


# ============== API ENDPOINTS ==============

'''
@require_http_methods(["GET"])
def api_course_list(request):
    """API endpoint to get course list"""
    courses = Course.objects.filter(is_active=True)
    
    # Apply filters
    category = request.GET.get('category')
    course_type = request.GET.get('type')
    search = request.GET.get('q')
    
    if category:
        courses = courses.filter(category__slug=category)
    if course_type:
        courses = courses.filter(course_type=course_type)
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Pagination
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    offset = (page - 1) * limit
    
    courses = courses[offset:offset + limit]
    
    data = []
    for course in courses:
        data.append({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'description': course.description[:200],
            'price': str(course.price) if course.price else None,
            'discount_price': str(course.discount_price) if course.discount_price else None,
            'thumbnail': course.thumbnail.url if course.thumbnail else None,
            'course_type': course.course_type,
            'age_group': course.age_group,
            'duration_weeks': course.recommended_duration_weeks,
            'is_featured': course.is_featured,
        })
    
    return JsonResponse({
        'success': True,
        'courses': data,
        'page': page,
        'has_next': Course.objects.filter(is_active=True).count() > offset + limit,
    })


@require_http_methods(["GET"])
def api_course_detail(request, course_id):
    """API endpoint to get course details"""
    try:
        course = Course.objects.get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    
    reviews = course.reviews.filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    teachers_data = []
    for teacher in course.teachers.all():
        teacher_data = {
            'id': teacher.id,
            'name': teacher.get_full_name(),
            'email': teacher.email,
        }
        if hasattr(teacher, 'teacher_profile'):
            teacher_data.update({
                'rating': float(teacher.teacher_profile.rating),
                'total_reviews': teacher.teacher_profile.total_reviews,
                'experience': teacher.teacher_profile.years_of_experience,
            })
        teachers_data.append(teacher_data)
    
    data = {
        'id': course.id,
        'title': course.title,
        'title_bn': course.title_bn,
        'slug': course.slug,
        'description': course.description,
        'description_bn': course.description_bn,
        'syllabus': course.get_syllabus_sections(),
        'price': str(course.price) if course.price else None,
        'discount_price': str(course.discount_price) if course.discount_price else None,
        'course_type': course.course_type,
        'age_group': course.age_group,
        'duration_weeks': course.recommended_duration_weeks,
        'sessions_per_week': course.sessions_per_week,
        'session_duration': course.session_duration_minutes,
        'thumbnail': course.thumbnail.url if course.thumbnail else None,
        'preview_video': course.preview_video_url,
        'teachers': teachers_data,
        'rating': float(avg_rating),
        'total_reviews': reviews.count(),
        'is_featured': course.is_featured,
    }
    
    return JsonResponse({'success': True, 'course': data})


@require_http_methods(["GET"])
def api_course_videos(request, course_id):
    """API endpoint to get course videos"""
    try:
        course = Course.objects.get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    
    # Check if user has access
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = CourseEnrollment.objects.filter(
            student=request.user,
            course=course,
            status='active'
        ).exists()
    
    videos = course.videos.filter(is_active=True).order_by('order')
    
    # Filter based on enrollment status
    if not is_enrolled:
        videos = videos.filter(is_free=True)
    
    data = []
    for video in videos:
        data.append({
            'id': video.id,
            'title': video.title,
            'description': video.description,
            'video_url': video.video_url if is_enrolled or video.is_free else None,
            'duration': video.duration_minutes,
            'order': video.order,
            'is_free': video.is_free,
        })
    
    return JsonResponse({
        'success': True,
        'videos': data,
        'is_enrolled': is_enrolled,
    })


@login_required
@require_http_methods(["POST"])
def api_enroll(request):
    """API endpoint to enroll in a course"""
    data = json.loads(request.body)
    course_id = data.get('course_id')
    teacher_id = data.get('teacher_id')
    
    try:
        course = Course.objects.get(id=course_id, is_active=True)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    
    # Check if already enrolled
    if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
        return JsonResponse({'success': False, 'error': 'Already enrolled'}, status=400)
    
    teacher = None
    if teacher_id:
        try:
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            if teacher not in course.teachers.all():
                return JsonResponse({'success': False, 'error': 'Invalid teacher'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Teacher not found'}, status=404)
    
    # Create enrollment
    enrollment = CourseEnrollment.objects.create(
        student=request.user,
        course=course,
        teacher=teacher,
        status='pending' if not course.is_free else 'active',
    )
    
    if course.is_free:
        enrollment.started_at = timezone.now()
        enrollment.save()
    
    return JsonResponse({
        'success': True,
        'enrollment_id': enrollment.id,
        'redirect_url': '/payments/checkout/{}/'.format(course.id) if not course.is_free else '/dashboard/courses/',
    })


@login_required
@require_http_methods(["POST"])
def api_add_review(request):
    """API endpoint to add a review"""
    data = json.loads(request.body)
    course_id = data.get('course_id')
    rating = data.get('rating')
    title = data.get('title')
    comment = data.get('comment')
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Course not found'}, status=404)
    
    # Check if user is enrolled
    try:
        enrollment = CourseEnrollment.objects.get(
            student=request.user,
            course=course
        )
    except CourseEnrollment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Not enrolled'}, status=403)
    
    # Check if already reviewed
    existing_review = Review.objects.filter(
        course=course,
        student=request.user
    ).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.title = title
        existing_review.comment = comment
        existing_review.save()
        message = 'Review updated successfully'
    else:
        # Create new review
        Review.objects.create(
            course=course,
            student=request.user,
            teacher=enrollment.teacher,
            rating=rating,
            title=title,
            comment=comment,
            is_verified_purchase=True,
        )
        message = 'Review added successfully'
    
    return JsonResponse({
        'success': True,
        'message': message,
    })
    '''

# ============== API ENDPOINTS ==============