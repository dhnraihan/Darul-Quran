from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
import uuid

User = get_user_model()

class ClassSession(models.Model):
    """Model for managing individual class sessions"""
    
    PLATFORM_CHOICES = [
        ('teams', 'Microsoft Teams'),
        ('zoom', 'Zoom'),
        ('google_meet', 'Google Meet'),
        ('whatsapp', 'WhatsApp'),
        ('skype', 'Skype'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('rescheduled', _('Rescheduled')),
        ('no_show', _('No Show')),
    ]
    
    session_id = models.UUIDField(
        _('Session ID'),
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('Course')
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teaching_sessions',
        limit_choices_to={'user_type': 'teacher'},
        verbose_name=_('Teacher')
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='learning_sessions',
        limit_choices_to={'user_type': 'student'},
        verbose_name=_('Student')
    )
    date = models.DateField(_('Session Date'))
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    duration_minutes = models.PositiveIntegerField(
        _('Duration (minutes)'),
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(180)]
    )
    platform = models.CharField(
        _('Platform'),
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='teams'
    )
    meeting_link = models.URLField(
        _('Meeting Link'),
        blank=True,
        help_text=_('Video conference meeting link')
    )
    meeting_id = models.CharField(
        _('Meeting ID'),
        max_length=100,
        blank=True,
        help_text=_('Platform-specific meeting ID')
    )
    meeting_password = models.CharField(
        _('Meeting Password'),
        max_length=50,
        blank=True
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    topic = models.CharField(
        _('Session Topic'),
        max_length=200,
        blank=True
    )
    objectives = models.TextField(
        _('Learning Objectives'),
        blank=True
    )
    homework = models.TextField(
        _('Homework/Assignment'),
        blank=True
    )
    teacher_notes = models.TextField(
        _('Teacher Notes'),
        blank=True,
        help_text=_('Private notes for the teacher')
    )
    student_notes = models.TextField(
        _('Student Notes'),
        blank=True
    )
    attendance_marked = models.BooleanField(
        _('Attendance Marked'),
        default=False
    )
    student_attended = models.BooleanField(
        _('Student Attended'),
        default=False
    )
    teacher_attended = models.BooleanField(
        _('Teacher Attended'),
        default=False
    )
    recording_url = models.URLField(
        _('Recording URL'),
        blank=True,
        help_text=_('Link to session recording')
    )
    reminder_sent = models.BooleanField(
        _('Reminder Sent'),
        default=False
    )
    feedback_rating = models.PositiveIntegerField(
        _('Session Rating'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    feedback_comment = models.TextField(
        _('Feedback Comment'),
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sessions'
    )
    
    class Meta:
        verbose_name = _('Class Session')
        verbose_name_plural = _('Class Sessions')
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'start_time']),
            models.Index(fields=['teacher', 'date']),
            models.Index(fields=['student', 'date']),
            models.Index(fields=['status']),
        ]
        unique_together = [['teacher', 'date', 'start_time']]
    
    def __str__(self):
        return f"{self.course.title} - {self.date} {self.start_time}"
    
    @property
    def is_upcoming(self):
        """Check if session is upcoming"""
        from datetime import datetime
        session_datetime = timezone.make_aware(
            datetime.combine(self.date, self.start_time)
        )
        return session_datetime > timezone.now() and self.status == 'scheduled'
    
    @property
    def is_past(self):
        """Check if session is past"""
        from datetime import datetime
        session_datetime = timezone.make_aware(
            datetime.combine(self.date, self.end_time)
        )
        return session_datetime < timezone.now()
    
    @property
    def is_today(self):
        """Check if session is today"""
        return self.date == timezone.now().date()
    
    @property
    def can_join(self):
        """Check if session can be joined (within 15 minutes before start)"""
        from datetime import datetime
        if not self.is_today:
            return False
        
        session_datetime = timezone.make_aware(
            datetime.combine(self.date, self.start_time)
        )
        time_until = session_datetime - timezone.now()
        return timedelta(minutes=-15) <= time_until <= timedelta(minutes=60)
    
    def get_whatsapp_link(self):
        """Generate WhatsApp click-to-chat link"""
        if self.platform == 'whatsapp':
            if self.teacher.phone_number:
                phone = self.teacher.phone_number.replace('+', '').replace(' ', '')
                message = f"Hello, I'm ready for our {self.course.title} class scheduled at {self.start_time.strftime('%I:%M %p')}"
                return f"https://wa.me/{phone}?text={message}"
        return ""
    
    def get_duration_display(self):
        """Get human-readable duration"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
        return f"{minutes}m"
    
    def generate_meeting_link(self):
        """Generate meeting link based on platform"""
        if self.platform == 'teams':
            # Microsoft Teams integration would go here
            pass
        elif self.platform == 'zoom':
            # Zoom integration would go here
            pass
        elif self.platform == 'google_meet':
            # Google Meet integration would go here
            pass
        return self.meeting_link
    
    def send_reminder(self):
        """Send reminder to participants"""
        from .tasks import send_class_reminder
        if not self.reminder_sent:
            send_class_reminder.delay(self.id)
            self.reminder_sent = True
            self.save()


class TeacherAvailability(models.Model):
    """Manage teacher's available time slots"""
    
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]
    
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={'user_type': 'teacher'},
        verbose_name=_('Teacher')
    )
    day_of_week = models.IntegerField(
        _('Day of Week'),
        choices=DAYS_OF_WEEK
    )
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    is_active = models.BooleanField(_('Active'), default=True)
    max_sessions = models.PositiveIntegerField(
        _('Max Sessions'),
        default=10,
        help_text=_('Maximum number of sessions for this slot')
    )
    break_minutes = models.PositiveIntegerField(
        _('Break Between Sessions'),
        default=10,
        help_text=_('Minutes of break between sessions')
    )
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Teacher Availability')
        verbose_name_plural = _('Teacher Availabilities')
        ordering = ['day_of_week', 'start_time']
        unique_together = ['teacher', 'day_of_week', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"
    
    def get_available_slots(self, date):
        """Get available time slots for a specific date"""
        from datetime import datetime, timedelta
        
        # Check if date matches this day of week
        if date.weekday() != self.day_of_week:
            return []
        
        # Get existing sessions for this date
        existing_sessions = ClassSession.objects.filter(
            teacher=self.teacher,
            date=date,
            status__in=['scheduled', 'in_progress']
        ).values_list('start_time', 'end_time')
        
        # Generate available slots
        slots = []
        current_time = datetime.combine(date, self.start_time)
        end_time = datetime.combine(date, self.end_time)
        slot_duration = timedelta(minutes=30)  # Default slot duration
        
        while current_time + slot_duration <= end_time:
            slot_start = current_time.time()
            slot_end = (current_time + slot_duration).time()
            
            # Check if slot is available
            is_available = True
            for session_start, session_end in existing_sessions:
                if (slot_start >= session_start and slot_start < session_end) or \
                   (slot_end > session_start and slot_end <= session_end):
                    is_available = False
                    break
            
            if is_available:
                slots.append({
                    'start': slot_start,
                    'end': slot_end
                })
            
            current_time += slot_duration + timedelta(minutes=self.break_minutes)
        
        return slots


class Assessment(models.Model):
    """Multi-step assessment form for new students"""
    
    STATUS_CHOICES = [
        ('incomplete', _('Incomplete')),
        ('submitted', _('Submitted')),
        ('reviewed', _('Reviewed')),
        ('scheduled', _('Trial Scheduled')),
        ('enrolled', _('Enrolled')),
        ('rejected', _('Rejected')),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', _('Beginner')),
        ('elementary', _('Elementary')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    ]
    
    # Step 1 - Basic Info (Required)
    full_name = models.CharField(_('Full Name'), max_length=200)
    phone_number = models.CharField(_('Phone Number'), max_length=17)
    
    # Step 2 - Additional Info (Optional)
    email = models.EmailField(_('Email'), blank=True)
    preferred_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Preferred Course')
    )
    trial_date = models.DateField(
        _('Preferred Trial Date'),
        null=True,
        blank=True
    )
    trial_time = models.TimeField(
        _('Preferred Trial Time'),
        null=True,
        blank=True
    )
    current_level = models.CharField(
        _('Current Level'),
        max_length=20,
        choices=LEVEL_CHOICES,
        blank=True
    )
    age = models.PositiveIntegerField(
        _('Age'),
        null=True,
        blank=True,
        validators=[MinValueValidator(3), MaxValueValidator(100)]
    )
    notes = models.TextField(
        _('Additional Notes'),
        blank=True
    )
    
    # Parent Information (for minors)
    parent_name = models.CharField(
        _('Parent/Guardian Name'),
        max_length=200,
        blank=True
    )
    parent_phone = models.CharField(
        _('Parent Phone'),
        max_length=17,
        blank=True
    )
    parent_email = models.EmailField(
        _('Parent Email'),
        blank=True
    )
    
    # Learning Preferences
    preferred_days = models.JSONField(
        _('Preferred Days'),
        default=list,
        blank=True
    )
    preferred_time_slot = models.CharField(
        _('Preferred Time Slot'),
        max_length=20,
        blank=True,
        choices=[
            ('morning', _('Morning (6 AM - 12 PM)')),
            ('afternoon', _('Afternoon (12 PM - 6 PM)')),
            ('evening', _('Evening (6 PM - 10 PM)')),
        ]
    )
    learning_goals = models.TextField(
        _('Learning Goals'),
        blank=True
    )
    
    # Metadata
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='incomplete'
    )
    assigned_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assessments',
        limit_choices_to={'user_type': 'teacher'}
    )
    trial_session = models.OneToOneField(
        ClassSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessment_trial'
    )
    admin_notes = models.TextField(
        _('Admin Notes'),
        blank=True
    )
    notification_sent = models.BooleanField(
        _('Notification Sent'),
        default=False
    )
    followup_required = models.BooleanField(
        _('Follow-up Required'),
        default=False
    )
    followup_date = models.DateField(
        _('Follow-up Date'),
        null=True,
        blank=True
    )
    converted_to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assessment_profile'
    )
    source = models.CharField(
        _('Source'),
        max_length=50,
        blank=True,
        help_text=_('How did they hear about us?')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Assessment')
        verbose_name_plural = _('Assessments')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['assigned_teacher', 'status']),
        ]
    
    def __str__(self):
        return f"Assessment - {self.full_name} ({self.status})"
    
    def schedule_trial(self, teacher, date, time):
        """Schedule a trial session for this assessment"""
        if self.preferred_course:
            session = ClassSession.objects.create(
                course=self.preferred_course,
                teacher=teacher,
                student=self.converted_to_user or User.objects.get(email='trial@amarquran.com'),  # Placeholder user
                date=date,
                start_time=time,
                end_time=(datetime.combine(date, time) + timedelta(minutes=30)).time(),
                duration_minutes=30,
                platform='teams',
                status='scheduled',
                topic='Trial Class',
                teacher_notes=f'Trial class for {self.full_name}'
            )
            self.trial_session = session
            self.assigned_teacher = teacher
            self.status = 'scheduled'
            self.save()
            return session
        return None


class TeacherPerformance(models.Model):
    """Track teacher performance metrics"""
    
    teacher = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='performance',
        limit_choices_to={'user_type': 'teacher'}
    )
    total_sessions = models.PositiveIntegerField(default=0)
    completed_sessions = models.PositiveIntegerField(default=0)
    cancelled_sessions = models.PositiveIntegerField(default=0)
    no_show_sessions = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_students = models.PositiveIntegerField(default=0)
    active_students = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    month_earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    last_session_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Teacher Performance')
        verbose_name_plural = _('Teacher Performances')
        ordering = ['-average_rating', '-total_sessions']
    
    def __str__(self):
        return f"{self.teacher.get_full_name()} - Performance"
    
    def update_metrics(self):
        """Update performance metrics"""
        from courses.models import Review
        
        # Update session counts
        sessions = ClassSession.objects.filter(teacher=self.teacher)
        self.total_sessions = sessions.count()
        self.completed_sessions = sessions.filter(status='completed').count()
        self.cancelled_sessions = sessions.filter(status='cancelled').count()
        self.no_show_sessions = sessions.filter(status='no_show').count()
        
        # Update student counts
        self.active_students = sessions.filter(
            status='scheduled',
            date__gte=timezone.now().date()
        ).values('student').distinct().count()
        
        self.total_students = sessions.values('student').distinct().count()
        
        # Update ratings
        reviews = Review.objects.filter(teacher=self.teacher)
        if reviews.exists():
            self.average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
        
        # Update last session date
        last_session = sessions.filter(status='completed').order_by('-date').first()
        if last_session:
            self.last_session_date = last_session.date
        
        self.save()