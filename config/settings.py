"""Django settings for the fish_be product-dashboard backend.

Configuration is driven by environment variables via django-environ so the same
code runs across local, CI, and production without edits. See .env.example.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "django_filters",
    # Local
    "catalog",
    "bookings",
    "content",
    "uploads",
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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Postgres is mandatory — the design relies on JSONB fields and GinIndex.
DATABASES = {"default": env.db("DATABASE_URL")}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# Media (cover images, product images). In production this is fronted by
# django-storages / cloud object storage; locally it lands under MEDIA_ROOT.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework -------------------------------------------------
# Locked down by default: every endpoint requires admin unless it explicitly
# opts into AllowAny. Public endpoints must set their own throttles.
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAdminUser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "1000/min",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

# --- Object storage (R2) ---------------------------------------------------
# All media is routed through core.storage.get_storage(). "fake" is the safe
# default (in-memory) so dev/CI never touch R2; set STORAGE_BACKEND=r2 with the
# R2_* vars in production.
STORAGE_BACKEND = env("STORAGE_BACKEND", default="fake")
R2_CONFIG = {
    "ENDPOINT_URL": env("R2_ENDPOINT_URL", default=""),
    "ACCESS_KEY_ID": env("R2_ACCESS_KEY_ID", default=""),
    "SECRET_ACCESS_KEY": env("R2_SECRET_ACCESS_KEY", default=""),
    "BUCKET": env("R2_BUCKET", default=""),
    "PUBLIC_BASE_URL": env("R2_PUBLIC_BASE_URL", default=""),
}

# --- Celery ----------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
