"""
Django settings for AccesLab project.
"""

from pathlib import Path
from datetime import timedelta 
import os
import oracledb # Driver moderno

# ----------------------------------------------------------------------
# INICIALIZACIÓN DE ORACLE INSTANT CLIENT
# ----------------------------------------------------------------------
# CRUCIAL: Esto resuelve el TypeError 500 y la inestabilidad de conexión.
try:
    # 🚨 RUTA FINAL DE OCI.DLL APLICADA 🚨
    oracledb.init_oracle_client(lib_dir=r"C:\app\mipri\product\23ai\dbhomeFree\bin") 
except Exception:
    pass


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = 'django-insecure-(a-s14s88eap#(ivl2--_@_p-0)5ez1u)til4(@%hpt5e+$jy!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'usuarios',
    'maestros',
    'reservas',
    'rest_framework_simplejwt', 
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AccesLab.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AccesLab.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        
        'HOST': 'localhost', 
        'PORT': '1521',
        'NAME': 'FREE', # Este es el SERVICE_NAME que Oracle necesita
        
        'USER': 'C##_ACCESLAB_USER', 
        'PASSWORD': 'Wilder2004',
        
        # ⚠️ DEJAMOS EL DICCIONARIO OPTIONS VACÍO ⚠️
        'OPTIONS': {
             
        }
    }
}

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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication', 
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Configuración de expiración de tokens
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15), 
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}