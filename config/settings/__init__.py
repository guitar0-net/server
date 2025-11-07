# SPDX-FileCopyrightText: 2025 Andrey Kotlyar
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from pathlib import Path

import dj_database_url

from config.settings.logging import get_logging_config

from .base import get_settings

settings = get_settings()
LOGGING = get_logging_config(settings)
os.makedirs(settings.LOG_FILE_PATH.parent, exist_ok=True)

SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS or (["*"] if DEBUG else [])
TEMPLATES = settings.TEMPLATES

DATABASES = {"default": dj_database_url.parse(settings.DATABASE_URL, conn_max_age=600)}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

STATIC_URL = "/static/"
STATIC_ROOT = Path(settings.BASE_DIR) / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(settings.BASE_DIR) / "media"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
