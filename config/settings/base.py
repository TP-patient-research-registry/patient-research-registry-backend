"""Settings shared by all environments. Environment-specific overrides live in dev/prod/test."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

# --- Core -------------------------------------------------------------------------------------

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Public URL of the Next.js frontend; used for links in emails.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000").rstrip("/")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "guardian",
    "auditlog",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.mfa",
]
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.consents",
    "apps.studies",
    "apps.questionnaires",
    "apps.notifications",
    "apps.gdpr",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# CORS is off by default: nginx serves frontend and API from the same origin.
CORS_ENABLED = env.bool("CORS_ENABLED", default=False)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    *(["corsheaders.middleware.CorsMiddleware"] if CORS_ENABLED else []),
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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

# --- Database & cache -------------------------------------------------------------------------

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL},
}

# --- Auth -------------------------------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Session cookie auth only (no JWT / tokens).
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=int(timedelta(hours=12).total_seconds()))
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # the frontend reads `csrftoken` and sends it as X-CSRFToken
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# django-allauth (headless, browser client = session cookies only)
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SIGNUP_FORM_CLASS = "apps.accounts.forms.SignupForm"
ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"
HEADLESS_ONLY = True
HEADLESS_CLIENTS = ("browser",)
HEADLESS_SERVE_SPECIFICATION = True  # OpenAPI spec of the auth API at /api/auth/openapi.html
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{FRONTEND_URL}/verify-email?key={{key}}",
    "account_reset_password_from_key": f"{FRONTEND_URL}/reset-password?key={{key}}",
    "account_signup": f"{FRONTEND_URL}/register",
}
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes"]
MFA_TOTP_ISSUER = "Patient Research Registry"

# django-guardian: our User has no username, so disable the anonymous user object.
ANONYMOUS_USER_NAME = None

# --- Encryption of health data (GDPR art. 9) --------------------------------------------------
# Separate from SECRET_KEY so the session key can be rotated without losing encrypted data.
# Losing this key means losing the encrypted data: back it up separately from DB backups.
CRYPTOGRAPHY_KEY = env("FIELD_ENCRYPTION_KEY")

# --- Audit log --------------------------------------------------------------------------------

AUDITLOG_INCLUDE_ALL_MODELS = False
# Masked fields (health data) are logged as "changed" without their values.
AUDITLOG_MASK_CALLABLE = "apps.core.audit.mask_value"

# --- REST framework & OpenAPI -----------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    # Default deny: every view must declare its own permission classes explicitly.
    "DEFAULT_PERMISSION_CLASSES": ["apps.core.permissions.DenyAll"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "300/min"},
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Patient Research Registry API",
    "DESCRIPTION": "REST API connecting patients/volunteers with clinical research studies in Slovakia. "
    "Authentication endpoints (django-allauth headless) are documented at /api/auth/openapi.html.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Paths in the schema are relative to /api (frontend client uses baseUrl=/api).
    "SCHEMA_PATH_PREFIX": "/api",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVERS": [{"url": "/api"}],
    "COMPONENT_SPLIT_REQUEST": True,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "ENUM_NAME_OVERRIDES": {
        "RegionEnum": "apps.accounts.models.Region",
        "StudyStatusEnum": "apps.studies.models.StudyStatus",
        "EnrollmentStatusEnum": "apps.studies.models.EnrollmentStatus",
        "DeletionRequestStatusEnum": "apps.gdpr.models.DeletionRequestStatus",
    },
}

# --- Celery -----------------------------------------------------------------------------------

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = None
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "Europe/Bratislava"
CELERY_BEAT_SCHEDULE: dict = {
    # TODO: e.g. periodic processing of GDPR deletion requests, consent re-confirmation reminders.
}

# --- Email ------------------------------------------------------------------------------------

EMAIL_CONFIG = env.email("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Patient Research Registry <noreply@localhost>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --- i18n / static ----------------------------------------------------------------------------

LANGUAGE_CODE = "sk"
LANGUAGES = [("sk", "Slovenčina"), ("en", "English")]
TIME_ZONE = "Europe/Bratislava"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = env("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))

# --- Logging ----------------------------------------------------------------------------------
# Never log request bodies: they may contain health data.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"default": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
