"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import datetime
from celery.schedules import crontab

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
try:
    from .local import *  # (DEBUG, SECRET_KEY, DATABASES, ALLOWED_HOSTS)
except ImportError:
    from .production import *  # (DEBUG, SECRET_KEY, DATABASES, ALLOWED_HOSTS)
from .ckeditor import *
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/
# Application definition
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'rest_framework',
    'knox',
    'django_filters',
    'ckeditor_uploader',
    'ckeditor',
    'permission',
    'user',
    'two_factor',
    'django_otp',
    'phonenumber_field',
    'corsheaders',
    'utils',
    'core',
    'brand',
    'integration',
    'rest_framework.authtoken',
    'nested_admin',
    'django_json_widget',
    'rangefilter',
    'inventory',
    'cultivar',
    'labtest',
    'import_export',
    'multiselectfield',
    'fee_variable',
    'bill',
    'compliance_binder',
    'internal_onboarding',
    'seo',
    'drf_api_logger',
    'reversion',
    'reversion_extention',
    'knoxpasswordlessdrf'
    #'djangopasswordlessknox'
    # 'django_extensions',
    # 'rest_social_auth',
    # 'sslserver',
    # 'social_django',
]

MIDDLEWARE = ['querycount.middleware.QueryCountMiddleware'] if not PRODUCTION and DEBUG else []
MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsPostCsrfMiddleware',
    'drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware',
    'reversion_extention.middleware.RevisionMiddleware',
]

ROOT_URLCONF = 'core.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '..', '..', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'custom_button_tags': 'core.templatetags.custom_button_tags',
                'custom_submit_row_tags': 'core.templatetags.custom_submit_row_tags',
                # 'admin.urls': 'django.contrib.admin.templatetags.admin_urls',
            },

        },
    },
]

WSGI_APPLICATION = 'core.wsgi.APPLICATION'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, '..', '..', 'assets')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, '..', '..', 'static')
]

# REST FRAMEWORK KONX Settings
REST_KNOX = {
    'SECURE_HASH_ALGORITHM': 'cryptography.hazmat.primitives.hashes.SHA512',
    'AUTH_TOKEN_CHARACTER_LENGTH': 64,
    'TOKEN_TTL': datetime.timedelta(hours=12),  # None for never exp. token
    'USER_SERIALIZER': 'knox.serializers.UserSerializer',
    'TOKEN_LIMIT_PER_USER': None,
    'AUTO_REFRESH': False

}

# Custom user model
AUTH_USER_MODEL = 'user.User'

# Email setting
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


# CORS_ORIGIN_ALLOW_ALL = True  # Make to True to bypass all whitelisting URLs.


REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'knox.auth.TokenAuthentication',
        #'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.OrderingFilter', 'rest_framework.filters.SearchFilter',
                                'django_filters.rest_framework.DjangoFilterBackend',),
    'ORDERING_PARAM': 'order-by',
    'SEARCH_PARAM': 'q',
}

# Celery
TIME_ZONE = "UTC"
CELERY_TIMEZONE = TIME_ZONE

# rest-social-auth settings.You can add auth for FB, Github etc.
AUTHENTICATION_BACKENDS = (
    # 'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
    'permission.backends.CustomPermissionBackend',
)


FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler', ]

#For image upload ckeditor
AWS_QUERYSTRING_AUTH = False
CKEDITOR_ALLOW_NONIMAGE_FILES = False

CKEDITOR_BROWSE_SHOW_DIRS = True
CKEDITOR_RESTRICT_BY_DATE = False
DEFAULT_FILE_STORAGE = 'brand.storage.CKEditorMediaStorage' #storages.backends.s3boto3.S3Boto3Storage
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_RESTRICT_BY_USER = False

#you can also set it to 'SOMEORIGIN'
X_FRAME_OPTIONS = 'DENY'

SIMPLE_HISTORY_REVERT_DISABLED = True

PHONENUMBER_DEFAULT_REGION = 'US'
