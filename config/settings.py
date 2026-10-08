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

# Railway injects the app's public domain at runtime; trust it automatically so
# ALLOWED_HOSTS/CSRF don't need manual updates on every deploy.
RAILWAY_PUBLIC_DOMAIN = env("RAILWAY_PUBLIC_DOMAIN", default="")
if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RAILWAY_PUBLIC_DOMAIN]

CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", default=[])
if RAILWAY_PUBLIC_DOMAIN:
    CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, f"https://{RAILWAY_PUBLIC_DOMAIN}"]

# Railway terminates TLS at the edge and forwards plain HTTP with this header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

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
    "drf_spectacular",
    # Local
    "catalog",
    "bookings",
    "content",
    "uploads",
    "customers",
    "testimonials",
    "careers",
    "pricelist",
    "enquiries",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise serves static files directly from the app (no separate static host,
# which suits Railway). Compressed + hashed names enable far-future caching.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media (cover images, product images). In production this is fronted by
# django-storages / cloud object storage; locally it lands under MEDIA_ROOT.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework -------------------------------------------------
# Locked down by default: every endpoint requires admin unless it explicitly
# opts into AllowAny. Public endpoints must set their own throttles.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # JWT for customer accounts; session keeps Django admin + browsable API.
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
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

# ---------------------------------------------------------------------------
# drf-spectacular (OpenAPI)
# ---------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": env("API_TITLE", default="DNL Product Dashboard API"),
    "DESCRIPTION": (
        "Welcome to the DNL Product Dashboard & E-commerce API.\n\n"
        "### Key Architectural Features\n"
        "1. **Dynamic Category Schemas**: To support zero-migration scale-out of new business lines (fresh fish, frozen fish, poultry, veggies), "
        "categories define an OpenAPI-like custom validation schema in `field_schema` (JSONB). Products carry custom fields in `attributes` (JSONB), "
        "which are dynamically validated against their category's schema at write-time.\n"
        "2. **Atomic Inventory Reservation**: Bookings atomically reserve and decrement stock using `select_for_update()` to prevent overselling.\n"
        "3. **Image Optimization**: Media uploads are dynamically processed in Celery and stored directly in Cloud Storage (S3/R2).\n\n"
        "### Security & Permissions\n"
        "- **Public Endpoints**: Throttled and open to the public (`AllowAny`). Used for browsing and ordering.\n"
        "- **Admin/Staff Endpoints**: Locked down to authenticated administrative users (`IsAdminUser`).\n"
        "- **Customer Endpoints**: Require token authentication to view order history and profile.\n\n"
        "### Authentication\n"
        "Include the header `Authorization: Token <your_token>` for authenticated requests."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        # Shows the operation-filter search box above the tag list — type to
        # filter endpoints by path/tag (Swagger UI has no full-text search
        # across descriptions/examples, just this).
        "filter": True,
        "displayOperationId": False,
    },
    "TAGS": [
        {
            "name": "Public - Catalog",
            "description": "Browse categories and products available for sale.",
        },
        {
            "name": "Admin - Catalog",
            "description": "Manage products, dynamic category schemas, and inventory settings.",
        },
        {
            "name": "Public - Bookings",
            "description": "Submit and reserve bookings for dynamic inventory items.",
        },
        {
            "name": "Admin - Bookings",
            "description": "View, confirm, fulfill, or cancel bookings in the fulfillment pipeline.",
        },
        {
            "name": "Public - Customers",
            "description": "Register user accounts and view authenticated profiles and orders.",
        },
        {
            "name": "Admin - Customers",
            "description": "Manage customers, order history, and view registration trends.",
        },
        {
            "name": "Public - Content",
            "description": "Read published articles and announcements.",
        },
        {
            "name": "Admin - Content",
            "description": "Publish, edit, draft, and delete content and articles.",
        },
        {
            "name": "Public - Enquiries",
            "description": "Submit enquiries and contact requests.",
        },
        {
            "name": "Admin - Enquiries",
            "description": "Track, moderate, and manage contact enquiries.",
        },
        {
            "name": "Public - Testimonials",
            "description": "View approved testimonials or submit a new one.",
        },
        {
            "name": "Admin - Testimonials",
            "description": "Approve, moderate, reorder, or delete testimonials.",
        },
        {
            "name": "Public - Price List",
            "description": "Download or view metadata for the latest price list.",
        },
        {
            "name": "Admin - Price List",
            "description": "Upload new price list files and view upload history.",
        },
        {
            "name": "Public - Careers",
            "description": "View published job postings and career openings.",
        },
        {
            "name": "Admin - Careers",
            "description": "Manage career openings and job descriptions.",
        },
        {
            "name": "Public - Uploads",
            "description": "View metadata for uploaded image files.",
        },
        {
            "name": "Admin - Uploads",
            "description": "Upload, delete, and manage product and article images.",
        },
    ],
    "ENUM_NAME_OVERRIDES": {
        "BookingStatusEnum": "bookings.enums.BookingStatus",
        "ArticleStatusEnum": "content.enums.ArticleStatus",
        "TestimonialStatusEnum": "testimonials.enums.TestimonialStatus",
        "ImageStatusEnum": "uploads.enums.ImageStatus",
        "JobStatusEnum": "careers.enums.JobStatus",
        "EmploymentTypeEnum": "careers.enums.EmploymentType",
    },
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

# --- Email -----------------------------------------------------------------
# Console backend by default so dev/CI never send real mail; set EMAIL_BACKEND to
# the SMTP backend with the EMAIL_* vars in production (Railway env).
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@dnl.local")

# Inbox routing — where each notification type is delivered (see core.notifications).
DNL_ORDER_INBOX = env("DNL_ORDER_INBOX", default="orders@dnl.local")
DNL_GENERAL_INBOX = env("DNL_GENERAL_INBOX", default="info@dnl.local")
DNL_CAREERS_INBOX = env("DNL_CAREERS_INBOX", default="careers@dnl.local")
DNL_ADMIN_INBOX = env("DNL_ADMIN_INBOX", default="admin@dnl.local")
