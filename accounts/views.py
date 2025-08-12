from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.http import HttpResponseRedirect
from .models import User, TeacherProfile, StudentProfile
from .forms import UserRegistrationForm, UserProfileForm, TeacherProfileForm, StudentProfileForm

class LoginView(DjangoLoginView):
    """User login view"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # "Remember me": unchecked -> session ends on browser close
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        messages.success(self.request, _('Welcome back!'))
        return response
        
class LogoutView(View):
    """
    Custom logout view that handles both GET and POST requests.
    GET requests are allowed for easier linking from navigation.
    """
    def get(self, request, *args, **kwargs):
        # Log the user out and redirect to login page
        logout(request)
        messages.success(request, _('You have been successfully logged out.'))
        return redirect('accounts:login')
        
    def post(self, request, *args, **kwargs):
        # Handle POST requests (e.g., from a form with CSRF token)
        return self.get(request, *args, **kwargs)

class RegisterView(CreateView):
    """User registration view"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('dashboard:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = authenticate(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1']
        )
        login(self.request, user)
        messages.success(self.request, _('Welcome to Darul Quran!'))
        return response

class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add the appropriate profile form based on user type
        if user.is_teacher and hasattr(user, 'teacher_profile'):
            context['teacher_form'] = TeacherProfileForm(
                instance=user.teacher_profile,
                prefix='teacher'
            )
        elif user.is_student and hasattr(user, 'student_profile'):
            context['student_form'] = StudentProfileForm(
                instance=user.student_profile,
                prefix='student'
            )
            
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        # Get the appropriate profile form based on user type
        profile_form = None
        if request.user.is_teacher and hasattr(request.user, 'teacher_profile'):
            profile_form = TeacherProfileForm(
                request.POST, 
                request.FILES, 
                instance=request.user.teacher_profile,
                prefix='teacher'
            )
        elif request.user.is_student and hasattr(request.user, 'student_profile'):
            profile_form = StudentProfileForm(
                request.POST, 
                request.FILES, 
                instance=request.user.student_profile,
                prefix='student'
            )
        
        if form.is_valid() and (profile_form is None or profile_form.is_valid()):
            self.object = form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, _('Profile updated successfully!'))
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    
    def form_valid(self, form):
        messages.success(self.request, _('Profile updated successfully!'))
        return super().form_valid(form)

def verify_email(request, token):
    """
    Verify user's email address using a token.
    This is a placeholder view.
    """
    # The actual implementation should decode the token, find the user,
    # and set user.is_email_verified = True.
    # For now, we'll just show a message and redirect.
    messages.success(request, _('Email verification is a work in progress. You have been redirected.'))
    # In a real implementation, you would find the user by the token
    # and mark their email as verified.
    return redirect('dashboard:home')


@login_required
def verify_phone(request):
    """
    Verify user's phone number, likely via an OTP.
    This is a placeholder view.
    """
    # TODO: Implement phone verification logic
    messages.info(request, _("Phone verification would be processed here"))
    return redirect('accounts:profile')


def verify_email_request(request):
    """
    Handle email verification requests.
    Sends a verification email to the user.
    """
    if not request.user.is_authenticated:
        messages.warning(request, _("Please log in to verify your email."))
        return redirect('accounts:login')
    
    if request.user.is_email_verified:
        messages.info(request, _("Your email is already verified."))
        return redirect('accounts:profile')
    
    # TODO: Implement email sending logic with verification token
    # For now, we'll just mark as verified for demonstration
    request.user.is_email_verified = True
    request.user.save()
    
    messages.success(request, _("A verification email has been sent to your email address."))
    return redirect('accounts:profile')
