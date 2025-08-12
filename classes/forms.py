from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ClassSession, Assessment, TeacherAvailability

class ClassSessionForm(forms.ModelForm):
    """Form for creating/editing class sessions"""
    
    class Meta:
        model = ClassSession
        fields = ['date', 'start_time', 'end_time', 'platform', 'topic',
                 'objectives', 'homework', 'teacher_notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'time'
            }),
            'platform': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'topic': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Session topic')
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Learning objectives for this session')
            }),
            'homework': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Homework or assignments')
            }),
            'teacher_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Private notes (not visible to student)')
            }),
        }


class AssessmentForm(forms.ModelForm):
    """Multi-step assessment form"""
    
    class Meta:
        model = Assessment
        fields = ['full_name', 'phone_number', 'email', 'preferred_course',
                 'trial_date', 'trial_time', 'current_level', 'age', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Your full name'),
                'required': True,
                'x-model': 'formData.full_name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('+880 1XXX-XXXXXX'),
                'required': True,
                'x-model': 'formData.phone_number'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Email address (optional)'),
                'x-model': 'formData.email'
            }),
            'preferred_course': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'x-model': 'formData.preferred_course'
            }),
            'trial_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'date',
                'x-model': 'formData.trial_date'
            }),
            'trial_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'time',
                'x-model': 'formData.trial_time'
            }),
            'current_level': forms.Select(
                choices=[
                    ('', _('Select your level')),
                    ('beginner', _('Beginner')),
                    ('elementary', _('Elementary')),
                    ('intermediate', _('Intermediate')),
                    ('advanced', _('Advanced')),
                ],
                attrs={
                    'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                    'x-model': 'formData.current_level'
                }
            ),
            'age': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Age'),
                'min': 3,
                'max': 100,
                'x-model': 'formData.age'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Any additional information you\'d like to share?'),
                'x-model': 'formData.notes'
            }),
        }


class TeacherAvailabilityForm(forms.ModelForm):
    """Form for teacher availability slots"""
    
    class Meta:
        model = TeacherAvailability
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'time'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'mr-2'
            }),
        }