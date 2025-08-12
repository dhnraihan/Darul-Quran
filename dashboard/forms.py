from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DashboardWidget, Announcement

class DashboardWidgetForm(forms.ModelForm):
    """Form for creating/editing dashboard widgets"""
    
    class Meta:
        model = DashboardWidget
        fields = ['widget_type', 'title', 'position', 'settings', 'is_visible']
        widgets = {
            'widget_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Widget Title')
            }),
            'position': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'min': 0
            }),
            'is_visible': forms.CheckboxInput(attrs={
                'class': 'mr-2'
            }),
        }


class AnnouncementForm(forms.ModelForm):
    """Form for creating announcements"""
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'target_audience', 
                 'is_active', 'start_date', 'end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 4
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'target_audience': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'mr-2'
            }),
        }


class ReportFilterForm(forms.Form):
    """Form for filtering reports"""
    
    REPORT_TYPES = [
        ('users', _('Users Report')),
        ('payments', _('Payments Report')),
        ('sessions', _('Sessions Report')),
        ('enrollments', _('Enrollments Report')),
        ('earnings', _('Earnings Report')),
    ]
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
        })
    )
    
    format_type = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
        })
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'type': 'date'
        })
    )