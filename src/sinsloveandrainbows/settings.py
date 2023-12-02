"""
Django settings for sinsloveandrainbows project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from subprocess import check_output

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
CURRENT_BRANCH = check_output(['git', 'symbolic-ref', '--short', 'HEAD']).decode('utf8')[0:-1]

DEBUG = CURRENT_BRANCH != 'production'
ALLOWED_HOSTS = [
    "127.0.0.1", "localhost",
    "sinsloveandrainbows.com", "www.sinsloveandrainbows.com", "api.sinsloveandrainbows.com",
    "sinsloveandrainbows.eu", "www.sinsloveandrainbows.eu", "api.sinsloveandrainbows.eu",
] if not DEBUG else ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'corsheaders',

    # third party
    'ninja_extra',
    'ninja_jwt',
    'markdownfield',

    # custom
    'api',
    'slrportal',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'slrportal.auth_middleware.CustomQueryParamMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sinsloveandrainbows.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'sinsloveandrainbows.wsgi.application'

CORS_ALLOW_ALL_ORIGINS = True

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / f'{CURRENT_BRANCH}.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_ROOT = BASE_DIR / 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'staticfiles',
]

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SITE_ID = 1
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# # Django allauth
# ACCOUNT_AUTHENTICATION_METHOD = 'email'
# ACCOUNT_USERNAME_REQUIRED = False
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_CONFIRM_EMAIL_ON_GET = True
# ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = '/'
# ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # switch to mandatory!
# ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 300
# ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
# ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = True
# ACCOUNT_EMAIL_SUBJECT_PREFIX = '[Biagiodistefano] '

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'slrportal.auth_backend.CustomQueryParamAuthentication',
)

# Email settings
# EMAIL_HOST = config('BIAGIODISTEFANO_EMAIL_HOST')
# EMAIL_PORT = config('BIAGIODISTEFANO_EMAIL_PORT', default=587, cast=int)
# EMAIL_HOST_USER = config('BIAGIODISTEFANO_EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = config('BIAGIODISTEFANO_EMAIL_HOST_PASSWORD')
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = config('BIAGIODISTEFANO_DEFAULT_FROM_EMAIL')
DRY_EMAILS = DEBUG
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

SLR_USE_AUTH = config("SLR_USE_AUTH", default=True, cast=bool)

DATA_UPLOAD_MAX_MEMORY_SIZE = int(
    (
        config("DATA_UPLOAD_MAX_SIZE_MB", cast=float, default=10) * 1024 * 1024
    )
)  # 1 MB

ADMIN_URL = config("ADMIN_URL", default="admin/")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
AUTH_USER_MODEL = "api.Person"

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
