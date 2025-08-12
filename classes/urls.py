from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    # Assessment
    path('assessment/', views.assessment_form, name='assessment'),
    path('assessment/submit/', views.submit_assessment, name='submit_assessment'),
    
    # Schedule
    path('schedule/', views.class_schedule, name='schedule'),
    path('schedule/calendar/', views.calendar_view, name='calendar'),
    
    # Session management
    path('session/<uuid:session_id>/', views.class_detail, name='session_detail'),
    path('session/<uuid:session_id>/reschedule/', views.reschedule_session, name='reschedule'),
    path('session/<uuid:session_id>/cancel/', views.cancel_session, name='cancel'),
    path('session/<uuid:session_id>/complete/', views.complete_session, name='complete'),
    
    # Teacher availability
    path('availability/', views.teacher_availability, name='availability'),
    path('availability/<int:teacher_id>/', views.get_teacher_availability, name='get_availability'),
    
    # Booking
    path('book/', views.book_class, name='book'),
    path('book/confirm/', views.confirm_booking, name='confirm_booking'),
    
    # API endpoints
    # path('api/sessions/', views.api_sessions_list, name='api_sessions'),
    # path('api/session/<uuid:session_id>/', views.api_session_detail, name='api_session_detail'),
    # path('api/availability/<int:teacher_id>/', views.api_teacher_availability, name='api_availability'),
    # path('api/book/', views.api_book_session, name='api_book'),
    # path('api/reschedule/', views.api_reschedule, name='api_reschedule'),
]