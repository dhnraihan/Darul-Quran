from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, TeacherProfile, StudentProfile
from .forms import UserRegistrationForm, UserProfileForm, TeacherProfileForm
from django.contrib.auth.views import LoginView as DjangoLoginView

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
        messages.success(self.request, _('Welcome to Amar Quran!'))
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
    # The actual implementation would involve a form to enter an OTP
    # sent to the user's phone.
    messages.info(request, _('Phone verification is not yet implemented.'))
    return redirect('accounts:profile')


