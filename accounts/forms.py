from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User, TeacherProfile, StudentProfile

class UserRegistrationForm(UserCreationForm):
    """Custom user registration form"""
    
    USER_TYPE_CHOICES = [
        ('student', _('I am a Student')),
        ('teacher', _('I am a Teacher')),
    ]
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': _('Email Address')
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': _('First Name')
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': _('Last Name')
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': _('+880 1XXX-XXXXXX')
        })
    )
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        })
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': _('Password')
        })
    )
    
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
            'placeholder': _('Confirm Password')
        })
    )
    
    terms_agreed = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 
                 'user_type', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = None  # We don't use username
        
        if commit:
            user.save()
            
            # Create profile based on user type
            if user.user_type == 'teacher':
                TeacherProfile.objects.create(user=user)
            elif user.user_type == 'student':
                StudentProfile.objects.create(user=user)
        
        return user


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'date_of_birth',
                 'address', 'city', 'country', 'profile_picture', 'preferred_language']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'country': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
        }


class TeacherProfileForm(forms.ModelForm):
    """Form for teacher profile"""
    
    specializations = forms.MultipleChoiceField(
        choices=[
            ('quran_recitation', _('Qur\'an Recitation')),
            ('hifz', _('Hifz (Memorization)')),
            ('tajweed', _('Tajweed')),
            ('arabic', _('Arabic Language')),
            ('islamic_studies', _('Islamic Studies')),
            ('aqeedah', _('Aqeedah')),
            ('fiqh', _('Fiqh')),
            ('hadith', _('Hadith')),
            ('tafseer', _('Tafseer')),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    languages = forms.MultipleChoiceField(
        choices=[
            ('bengali', _('Bengali')),
            ('english', _('English')),
            ('arabic', _('Arabic')),
            ('urdu', _('Urdu')),
            ('hindi', _('Hindi')),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    class Meta:
        model = TeacherProfile
        fields = ['bio', 'education', 'qualifications', 'specializations',
                 'languages', 'years_of_experience', 'hourly_rate', 
                 'verification_documents', 'timezone']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 4,
                'placeholder': _('Tell us about yourself...')
            }),
            'education': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Your educational background...')
            }),
            'qualifications': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('Your qualifications and certifications...')
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'min': 0
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'step': '0.01',
                'placeholder': _('Hourly rate in BDT')
            }),
            'verification_documents': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'timezone': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
            }),
        }


class StudentProfileForm(forms.ModelForm):
    """Form for student profile"""
    
    AGE_GROUP_CHOICES = [
        ('5-7', '5-7 years'),
        ('8-10', '8-10 years'),
        ('11-13', '11-13 years'),
        ('14-16', '14-16 years'),
        ('17-19', '17-19 years'),
        ('20+', '20+ years'),
    ]
    
    CURRENT_LEVEL_CHOICES = [
        ('beginner', _('Beginner')),
        ('elementary', _('Elementary')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    ]
    
    age_group = forms.ChoiceField(
        choices=AGE_GROUP_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
        required=False,
        label=_('Age Group')
    )
    
    current_level = forms.ChoiceField(
        choices=CURRENT_LEVEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500'
        }),
        required=True,
        label=_('Current Level')
    )
    
    class Meta:
        model = StudentProfile
        fields = [
            'age_group', 
            'current_level', 
            'learning_goals',
            'parent_name', 
            'parent_email', 
            'parent_phone',
            'preferred_class_time',
            'notes'
        ]
        widgets = {
            'learning_goals': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': _('What are your learning goals?')
            }),
            'parent_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Parent/Guardian Name')
            }),
            'parent_email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Parent/Guardian Email')
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Parent/Guardian Phone')
            }),
            'preferred_class_time': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'placeholder': _('Preferred class time (e.g., Weekdays after 4 PM)')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': _('Any additional notes or special requirements')
            }),
        }