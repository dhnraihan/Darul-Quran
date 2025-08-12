from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    
    # API endpoints (not translated)
    # path('api/', include('api.urls')),
    # path('webhooks/', include('webhooks.urls')),
]

# Translated URL patterns
urlpatterns += i18n_patterns(
    path('', views.home, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('classes/', include('classes.urls', namespace='classes')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    
    # Static pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('teachers/', views.teachers, name='teachers'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Custom error handlers
handler404 = 'amar_quran.views.handler404'
handler500 = 'amar_quran.views.handler500'