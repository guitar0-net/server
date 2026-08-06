# SPDX-FileCopyrightText: 2025-2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Initialize settings and configure derived attributes."""

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

from config.settings.logging import get_logging_config

from .base import get_settings

settings = get_settings()
LOGGING = get_logging_config(settings)
os.makedirs(settings.LOG_FILE_PATH.parent, exist_ok=True)

VERSION: str = settings.VERSION
GIT_SHA: str = settings.GIT_SHA
BUILD_DATETIME: str = settings.BUILD_DATETIME

SECRET_KEY = settings.SECRET_KEY
DEBUG = settings.DEBUG
ALLOWED_HOSTS = settings.ALLOWED_HOSTS or (["*"] if DEBUG else [])
CSRF_TRUSTED_ORIGINS = settings.CSRF_TRUSTED_ORIGINS
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
    "rest_framework_simplejwt.token_blacklist",
    "markdownx",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "apps.metrics",
    "apps.accounts",
    "apps.chords",
    "apps.schemes",
    "apps.songs",
    "apps.lessons",
    "apps.courses",
    "apps.announcements",
    "apps.sync",
    "apps.donations",
]

MIDDLEWARE = [
    "apps.metrics.middleware.PrometheusMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

AUTH_USER_MODEL = "accounts.User"

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
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "30/minute",
        "user": "150/minute",
        # Each call verifies against Google Play/App Store Server API, so
        # this needs to be much stricter than the general anon rate.
        "donation_verify": "5/minute",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.GuitarPagination",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Guitar0 API",
    "DESCRIPTION": "Django REST API for guitar0.net platform",
    "VERSION": settings.VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "ENUM_GENERATE_CHOICE_DESCRIPTION": True,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

GOOGLE_CLIENT_ID: str | None = settings.GOOGLE_CLIENT_ID

GOOGLE_PLAY_PACKAGE_NAME: str | None = settings.GOOGLE_PLAY_PACKAGE_NAME
GOOGLE_PLAY_SERVICE_ACCOUNT_INFO: str | None = settings.GOOGLE_PLAY_SERVICE_ACCOUNT_INFO

APPLE_BUNDLE_ID: str | None = settings.APPLE_BUNDLE_ID
APPLE_APP_APPLE_ID: int | None = settings.APPLE_APP_APPLE_ID

if settings.ENVIRONMENT in {"staging", "production"}:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
        "rest_framework.renderers.JSONRenderer",
    ]
