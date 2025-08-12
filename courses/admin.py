from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import CourseCategory, Course, CourseEnrollment, Review, CourseVideo

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'name_bn']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'course_type', 'price_display', 
                   'age_group', 'is_featured', 'is_active', 'created_at']
    list_filter = ['course_type', 'category', 'age_group', 'is_featured', 
                  'is_active', 'created_at']
    search_fields = ['title', 'title_bn', 'description', 'description_bn']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['teachers']
    ordering = ['-is_featured', '-created_at']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'title_bn', 'slug', 'category', 'course_type')
        }),
        (_('Description'), {
            'fields': ('description', 'description_bn', 'syllabus')
        }),
        (_('Pricing'), {
            'fields': ('price', 'discount_price')
        }),
        (_('Course Details'), {
            'fields': ('age_group', 'recommended_duration_weeks', 
                      'sessions_per_week', 'session_duration_minutes')
        }),
        (_('Media'), {
            'fields': ('thumbnail', 'preview_video_url')
        }),
        (_('Settings'), {
            'fields': ('is_featured', 'is_active', 'teachers', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def price_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green;">Free</span>')
        elif obj.discount_price:
            return format_html(
                '<strike>৳{}</strike> <strong>৳{}</strong>',
                obj.price, obj.discount_price
            )
        else:
            return f'৳{obj.price}'
    price_display.short_description = _('Price')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'teacher', 'status', 
                   'progress_percentage', 'enrolled_at']
    list_filter = ['status', 'enrolled_at', 'started_at']
    search_fields = ['student__email', 'course__title', 'teacher__email']
    raw_id_fields = ['student', 'course', 'teacher']
    ordering = ['-enrolled_at']
    
    fieldsets = (
        (_('Enrollment Info'), {
            'fields': ('student', 'course', 'teacher', 'status')
        }),
        (_('Progress'), {
            'fields': ('progress_percentage', 'completed_lessons')
        }),
        (_('Dates'), {
            'fields': ('enrolled_at', 'started_at', 'completed_at')
        }),
        (_('Additional'), {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ['enrolled_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'course', 'teacher')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'teacher', 'rating_stars', 
                   'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['student__email', 'course__title', 'title', 'comment']
    raw_id_fields = ['student', 'course', 'teacher']
    ordering = ['-created_at']
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def rating_stars(self, obj):
        return format_html('⭐' * obj.rating)
    rating_stars.short_description = _('Rating')
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews approved.')
    approve_reviews.short_description = _('Approve selected reviews')
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} reviews disapproved.')
    disapprove_reviews.short_description = _('Disapprove selected reviews')


@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'duration_minutes', 'order', 
                   'is_free', 'is_active']
    list_filter = ['is_free', 'is_active', 'course']
    search_fields = ['title', 'description', 'course__title']
    ordering = ['course', 'order']