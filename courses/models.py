from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import json

User = get_user_model()

class CourseCategory(models.Model):
    """Categories for courses"""
    name = models.CharField(_('Category Name'), max_length=100)
    name_bn = models.CharField(_('Category Name (Bengali)'), max_length=100, blank=True)
    slug = models.SlugField(_('Slug'), unique=True)
    description = models.TextField(_('Description'), blank=True)
    icon = models.CharField(_('Icon Class'), max_length=50, blank=True)
    order = models.PositiveIntegerField(_('Display Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        verbose_name = _('Course Category')
        verbose_name_plural = _('Course Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    """Course model for different packages"""
    
    COURSE_TYPE_CHOICES = [
        ('hifz', _('Hifz (Memorization)')),
        ('recitation', _('Proper Qur\'an Recitation')),
        ('arabic', _('Arabic Language')),
        ('aqeedah', _('Aqeedah (Islamic Belief)')),
        ('fiqh', _('Fiqh (Islamic Jurisprudence)')),
        ('hadith', _('Hadith Studies')),
        ('tafseer', _('Tafseer (Qur\'an Interpretation)')),
        ('islamic_studies', _('General Islamic Studies')),
    ]
    
    AGE_GROUP_CHOICES = [
        ('5-7', '5-7 years'),
        ('8-10', '8-10 years'),
        ('11-13', '11-13 years'),
        ('14-16', '14-16 years'),
        ('17-19', '17-19 years'),
        ('20+', '20+ years'),
        ('all', 'All ages'),
    ]
    
    title = models.CharField(_('Course Title'), max_length=200)
    title_bn = models.CharField(_('Course Title (Bengali)'), max_length=200, blank=True)
    slug = models.SlugField(_('Slug'), unique=True)
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses'
    )
    course_type = models.CharField(
        _('Course Type'),
        max_length=20,
        choices=COURSE_TYPE_CHOICES
    )
    description = models.TextField(_('Description'))
    description_bn = models.TextField(_('Description (Bengali)'), blank=True)
    syllabus = models.JSONField(
        _('Syllabus'),
        default=dict,
        help_text=_('Course syllabus with sections and lessons')
    )
    price = models.DecimalField(
        _('Price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Leave blank for free courses')
    )
    discount_price = models.DecimalField(
        _('Discount Price'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    age_group = models.CharField(
        _('Age Group'),
        max_length=10,
        choices=AGE_GROUP_CHOICES,
        default='all'
    )
    recommended_duration_weeks = models.PositiveIntegerField(
        _('Recommended Duration (weeks)'),
        default=12
    )
    sessions_per_week = models.PositiveIntegerField(
        _('Sessions per Week'),
        default=3
    )
    session_duration_minutes = models.PositiveIntegerField(
        _('Session Duration (minutes)'),
        default=30
    )
    thumbnail = models.ImageField(
        _('Thumbnail'),
        upload_to='course_thumbnails/',
        blank=True,
        null=True
    )
    preview_video_url = models.URLField(
        _('Preview Video URL'),
        blank=True
    )
    is_featured = models.BooleanField(_('Featured Course'), default=False)
    is_active = models.BooleanField(_('Active'), default=True)
    teachers = models.ManyToManyField(
        User,
        limit_choices_to={'user_type': 'teacher'},
        related_name='teaching_courses',
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def is_free(self):
        return self.price is None or self.price == 0
    
    @property
    def current_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price or 0
    
    def get_syllabus_sections(self):
        """Return syllabus sections as a list"""
        if isinstance(self.syllabus, dict):
            return self.syllabus.get('sections', [])
        return []


class CourseEnrollment(models.Model):
    """Track student enrollments in courses"""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_enrollments'
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    enrolled_at = models.DateTimeField(_('Enrolled At'), auto_now_add=True)
    started_at = models.DateTimeField(_('Started At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)
    progress_percentage = models.DecimalField(
        _('Progress %'),
        max_digits=5,
        decimal_places=2,
        default=0.00
    )
    completed_lessons = models.JSONField(
        _('Completed Lessons'),
        default=list
    )
    notes = models.TextField(_('Notes'), blank=True)
    
    class Meta:
        verbose_name = _('Course Enrollment')
        verbose_name_plural = _('Course Enrollments')
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title}"


class Review(models.Model):
    """Student reviews for courses and teachers"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        null=True,
        blank=True
    )
    rating = models.PositiveIntegerField(
        _('Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('Review Title'), max_length=200)
    comment = models.TextField(_('Comment'))
    is_verified_purchase = models.BooleanField(
        _('Verified Purchase'),
        default=False
    )
    is_approved = models.BooleanField(_('Approved'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        ordering = ['-created_at']
        unique_together = ['course', 'student']
    
    def __str__(self):
        return f"{self.student.email} - {self.course.title} ({self.rating}★)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update teacher rating if teacher is specified
        if self.teacher and hasattr(self.teacher, 'teacher_profile'):
            self.teacher.teacher_profile.update_rating()


class CourseVideo(models.Model):
    """Video content for courses"""
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    title = models.CharField(_('Video Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    video_url = models.URLField(_('Video URL'))
    duration_minutes = models.PositiveIntegerField(
        _('Duration (minutes)'),
        default=0
    )
    order = models.PositiveIntegerField(_('Order'), default=0)
    is_free = models.BooleanField(
        _('Free to Watch'),
        default=False,
        help_text=_('Make this video available for preview')
    )
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Course Video')
        verbose_name_plural = _('Course Videos')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"