from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # Password change
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html'
    ), name='password_change'),
    path('password/change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
    # The views for teacher_profile and student_profile were not defined.
    # Redirecting to the respective dashboards as a sensible default.
    path('teacher/profile/', RedirectView.as_view(pattern_name='dashboard:teacher_dashboard', permanent=False), name='teacher_profile'),
    path('student/profile/', RedirectView.as_view(pattern_name='dashboard:student_dashboard', permanent=False), name='student_profile'),
    
    # Verification
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
]