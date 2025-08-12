from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Course, CourseEnrollment, Review

class CourseForm(forms.ModelForm):
    """Form for creating/editing courses"""
    
    syllabus_sections = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'rows': 5,
            'placeholder': _('Enter syllabus sections, one per line')
        }),
        help_text=_('Enter each section/lesson on a new line'),
        required=False
    )
    
    class Meta:
        model = Course
        fields = ['title', 'title_bn', 'category', 'course_type', 'description', 
                 'description_bn', 'price', 'discount_price', 'age_group',
                 'recommended_duration_weeks', 'sessions_per_week', 
                 'session_duration_minutes', 'thumbnail', 'preview_video_url',
                 'is_featured', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'title_bn': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 4
            }),
            'description_bn': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 4
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'step': '0.01'
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'step': '0.01'
            }),
        }
    
    def save(self, commit=True):
        course = super().save(commit=False)
        
        # Process syllabus sections
        if self.cleaned_data.get('syllabus_sections'):
            sections = self.cleaned_data['syllabus_sections'].split('\n')
            course.syllabus = {
                'sections': [s.strip() for s in sections if s.strip()]
            }
        
        if commit:
            course.save()
        
        return course


class EnrollmentForm(forms.ModelForm):
    """Form for course enrollment"""
    
    class Meta:
        model = CourseEnrollment
        fields = ['teacher', 'notes']
        widgets = {
            'teacher': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Any special requirements or notes?')
            }),
        }


class ReviewForm(forms.ModelForm):
    """Form for submitting course reviews"""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, i) for i in range(1, 6)],
                attrs={'class': 'inline-flex'}
            ),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Review title')
            }),
            'comment': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 4,
                'placeholder': _('Share your experience...')
            }),
        }