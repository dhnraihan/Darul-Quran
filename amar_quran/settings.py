import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url
from django.utils.translation import gettext_lazy as _

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'modeltranslation',  # Must be before admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'corsheaders',
    'crispy_forms',
    'crispy_tailwind',
    'storages',
    'django_extensions',
    'debug_toolbar',
    # 'ratelimit',
    
    # Local apps
    'accounts.apps.AccountsConfig',
    'courses.apps.CoursesConfig',
    'classes.apps.ClassesConfig',
    'payments.apps.PaymentsConfig',
    'dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # For i18n
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_ratelimit.middleware.RatelimitMiddleware',
    # allauth requirement
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'amar_quran.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'amar_quran.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3')
    )
}

# Redis Cache & Celery
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    }
}

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('bn', _('Bengali')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AWS S3 Configuration (optional)
# if config('AWS_ACCESS_KEY_ID', default=None):
#     DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
#     AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
#     AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
#     AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
#     AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
#     AWS_S3_FILE_OVERWRITE = False
#     AWS_DEFAULT_ACL = None

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Login settings
SITE_ID = 1
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# django-allauth settings
# Authentication settings
# লগইন মেথড (শুধু ইমেইল)
ACCOUNT_LOGIN_METHODS = {'email'}

# সাইনআপের জন্য প্রয়োজনীয় ফিল্ড
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# ইমেইল অবশ্যই ইউনিক হবে
ACCOUNT_UNIQUE_EMAIL = True

# ইমেইল ভেরিফিকেশন বাধ্যতামূলক
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# ইউজারনেম ব্যবহার হবে না, ইমেইলই username ফিল্ড হবে
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'

# পাসওয়ার্ড চেঞ্জ হলে লগআউট করবে
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True

# সাইনআপে পাসওয়ার্ড দুইবার দিতে হবে
# ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

# সেশন মনে রাখবে
ACCOUNT_SESSION_REMEMBER = True


# Email Configuration
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
# EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = config('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# Stripe Configuration
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Payment Gateway Settings
# STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
# STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
# SSLCOMMERZ_STORE_ID = config('SSLCOMMERZ_STORE_ID', default='')
# SSLCOMMERZ_STORE_PASSWORD = config('SSLCOMMERZ_STORE_PASSWORD', default='')
# SSLCOMMERZ_SANDBOX = config('SSLCOMMERZ_SANDBOX', default=True, cast=bool)

# Twilio Settings
# TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
# TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
# TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER', default='')
# ADMIN_WHATSAPP_NUMBER = config('ADMIN_WHATSAPP_NUMBER', default='')

# Microsoft Teams Settings
# MICROSOFT_CLIENT_ID = config('MICROSOFT_CLIENT_ID', default='')
# MICROSOFT_CLIENT_SECRET = config('MICROSOFT_CLIENT_SECRET', default='')
# MICROSOFT_TENANT_ID = config('MICROSOFT_TENANT_ID', default='')

# Django Debug Toolbar
INTERNAL_IPS = ['127.0.0.1']
