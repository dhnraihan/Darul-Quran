from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

User = get_user_model()

class DashboardWidget(models.Model):
    """Customizable dashboard widgets for users"""
    WIDGET_TYPES = [
        ('stats', 'Statistics'),
        ('chart', 'Chart'),
        ('list', 'List'),
        ('calendar', 'Calendar'),
        ('progress', 'Progress'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_widgets')
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    position = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position', 'created_at']
        unique_together = ['user', 'widget_type', 'title']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class Announcement(models.Model):
    """System-wide announcements"""
    ANNOUNCEMENT_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('maintenance', 'Maintenance'),
    ]
    
    TARGET_AUDIENCES = [
        ('all', 'All Users'),
        ('students', 'Students Only'),
        ('teachers', 'Teachers Only'),
        ('admins', 'Admins Only'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPES, default='info')
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCES, default='all')
    priority = models.IntegerField(default=0, help_text="Higher priority announcements appear first")
    is_active = models.BooleanField(default=True)
    is_dismissible = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title
    
    def is_visible_to(self, user):
        """Check if announcement should be visible to a specific user"""
        if not self.is_active:
            return False
        
        now = timezone.now()
        if now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        if self.target_audience == 'all':
            return True
        elif self.target_audience == 'students' and user.is_student:
            return True
        elif self.target_audience == 'teachers' and user.is_teacher:
            return True
        elif self.target_audience == 'admins' and user.is_admin:
            return True
        
        return False


class ActivityLog(models.Model):
    """Track user activities for analytics and audit"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.timestamp}"


class NotificationPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Email notifications
    email_class_reminder = models.BooleanField(default=True)
    email_payment_receipt = models.BooleanField(default=True)
    email_course_updates = models.BooleanField(default=True)
    email_promotional = models.BooleanField(default=False)
    
    # SMS notifications
    sms_class_reminder = models.BooleanField(default=True)
    sms_payment_confirmation = models.BooleanField(default=True)
    
    # Push notifications
    push_enabled = models.BooleanField(default=True)
    push_class_reminder = models.BooleanField(default=True)
    push_messages = models.BooleanField(default=True)
    
    # Reminder timing
    reminder_minutes_before = models.IntegerField(default=30)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"