from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Course listings
    path('', views.course_list, name='list'),
    path('category/<slug:category_slug>/', views.course_list, name='by_category'),
    
    # Course details
    path('course/<slug:slug>/', views.course_detail, name='detail'),
    path('course/<slug:slug>/enroll/', views.enroll_course, name='enroll'),
    path('course/<slug:slug>/review/', views.add_review, name='add_review'),
    
    # Course content
    path('course/<slug:slug>/content/', views.course_content, name='content'),
    path('course/<slug:slug>/video/<int:video_id>/', views.watch_video, name='watch_video'),
    path('course/<slug:slug>/progress/', views.update_progress, name='update_progress'),
    
    # Teacher courses
    path('teacher/<int:teacher_id>/', views.teacher_courses, name='teacher_courses'),
    
    # API endpoints
    # path('api/courses/', views.api_course_list, name='api_list'),
    # path('api/course/<int:course_id>/', views.api_course_detail, name='api_detail'),
    # path('api/course/<int:course_id>/videos/', views.api_course_videos, name='api_videos'),
    # path('api/enroll/', views.api_enroll, name='api_enroll'),
    # path('api/review/', views.api_add_review, name='api_review'),
]