from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import DashboardWidget, Announcement, ActivityLog

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'widget_type', 'title', 'position', 'is_visible', 'created_at']
    list_filter = ['widget_type', 'is_visible', 'created_at']
    search_fields = ['user__email', 'title']
    ordering = ['user', 'position']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority_badge', 'target_audience', 'is_active', 'start_date', 'end_date', 'created_by']
    list_filter = ['priority', 'target_audience', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    
    def priority_badge(self, obj):
        colors = {
            'low': 'gray',
            'medium': 'blue',
            'high': 'orange',
            'urgent': 'red',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = _('Priority')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'ip_address']
    date_hierarchy = 'timestamp'
    readonly_fields = ['user', 'action', 'details', 'ip_address', 'user_agent', 'timestamp']
    
    def has_add_permission(self, request):
        return False