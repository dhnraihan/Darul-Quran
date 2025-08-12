# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, StudentProfile, TeacherProfile


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture', 'date_of_birth', 'address', 'city', 'country')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Status & Preferences'), {'fields': ('user_type', 'preferred_language', 'is_email_verified', 'is_phone_verified')}),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ('last_login', 'created_at', 'updated_at')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """Teacher Profile Admin"""
    list_display = ['user', 'rating', 'total_reviews', 'is_verified', 
                   'years_of_experience', 'created_at']
    list_filter = ['is_verified', 'rating', 'years_of_experience']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['-rating', '-total_reviews']
    readonly_fields = ['rating', 'total_reviews', 'created_at', 'updated_at']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Student Profile Admin"""
    list_display = ['user', 'age_group', 'current_level', 'created_at']
    list_filter = ['age_group', 'current_level']
    search_fields = ['user__email', 'user__first_name', 'user__last_name',
                    'parent_name', 'parent_email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']