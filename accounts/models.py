# accounts/models.py

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from PIL import Image
import os


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email as the username field"""
    
    USER_TYPE_CHOICES = [
        ('student', _('Student')),
        ('teacher', _('Teacher')),
        ('admin', _('Admin')),
    ]
    
    # Primary field
    email = models.EmailField(_('email address'), unique=True)
    
    # Personal Information
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    
    user_type = models.CharField(
        _('User Type'),
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        _('Phone Number'),
        validators=[phone_regex],
        max_length=17,
        blank=True
    )
    date_of_birth = models.DateField(_('Date of Birth'), null=True, blank=True)
    address = models.TextField(_('Address'), blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    country = models.CharField(_('Country'), max_length=100, blank=True)
    profile_picture = models.ImageField(
        _('Profile Picture'),
        upload_to='profile_pics/',
        blank=True,
        null=True
    )
    preferred_language = models.CharField(
        _('Preferred Language'),
        max_length=2,
        choices=[('en', 'English'), ('bn', 'Bengali')],
        default='en'
    )
    
    # Permissions
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    
    # Verification
    is_email_verified = models.BooleanField(_('Email Verified'), default=False)
    is_phone_verified = models.BooleanField(_('Phone Verified'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name or self.email
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_picture:
            self.resize_profile_picture()
    
    def resize_profile_picture(self):
        """Resize profile picture to optimize storage"""
        if self.profile_picture and os.path.exists(self.profile_picture.path):
            img = Image.open(self.profile_picture.path)
            if img.height > 500 or img.width > 500:
                output_size = (500, 500)
                img.thumbnail(output_size)
                img.save(self.profile_picture.path)
    
    @property
    def is_student(self):
        return self.user_type == 'student'
    
    @property
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    @property
    def is_admin(self):
        return self.user_type == 'admin' or self.is_superuser


class TeacherProfile(models.Model):
    """Extended profile for teachers"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    bio = models.TextField(_('Biography'), blank=True)
    education = models.TextField(_('Education'), blank=True)
    qualifications = models.TextField(_('Qualifications'), blank=True)
    specializations = models.JSONField(
        _('Specializations'),
        default=list,
        help_text=_('List of specialization areas')
    )
    languages = models.JSONField(
        _('Languages'),
        default=list,
        help_text=_('Languages spoken')
    )
    years_of_experience = models.PositiveIntegerField(
        _('Years of Experience'),
        default=0
    )
    hourly_rate = models.DecimalField(
        _('Hourly Rate'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    rating = models.DecimalField(
        _('Average Rating'),
        max_digits=3,
        decimal_places=2,
        default=0.00
    )
    total_reviews = models.PositiveIntegerField(
        _('Total Reviews'),
        default=0
    )
    is_verified = models.BooleanField(
        _('Verified Teacher'),
        default=False
    )
    verification_documents = models.FileField(
        _('Verification Documents'),
        upload_to='teacher_docs/',
        blank=True,
        null=True
    )
    available_slots = models.JSONField(
        _('Available Time Slots'),
        default=dict,
        help_text=_('Weekly available time slots')
    )
    timezone = models.CharField(
        _('Timezone'),
        max_length=50,
        default='Asia/Dhaka'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Teacher Profile')
        verbose_name_plural = _('Teacher Profiles')
        ordering = ['-rating', '-total_reviews']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Teacher"
    
    def update_rating(self):
        """Update average rating based on reviews"""
        try:
            from courses.models import Review
            reviews = Review.objects.filter(teacher=self.user)
            if reviews.exists():
                avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
                self.rating = round(avg_rating, 2)
                self.total_reviews = reviews.count()
                self.save()
        except ImportError:
            pass


class StudentProfile(models.Model):
    """Extended profile for students"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
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
    age_group = models.CharField(
        _('Age Group'),
        max_length=20,
        choices=[
            ('5-7', '5-7 years'),
            ('8-10', '8-10 years'),
            ('11-13', '11-13 years'),
            ('14-16', '14-16 years'),
            ('17-19', '17-19 years'),
            ('20+', '20+ years'),
        ],
        blank=True
    )
    current_level = models.CharField(
        _('Current Level'),
        max_length=50,
        choices=[
            ('beginner', _('Beginner')),
            ('elementary', _('Elementary')),
            ('intermediate', _('Intermediate')),
            ('advanced', _('Advanced')),
        ],
        default='beginner'
    )
    learning_goals = models.TextField(
        _('Learning Goals'),
        blank=True
    )
    preferred_class_time = models.CharField(
        _('Preferred Class Time'),
        max_length=50,
        blank=True
    )
    notes = models.TextField(
        _('Additional Notes'),
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Student Profile')
        verbose_name_plural = _('Student Profiles')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Student"