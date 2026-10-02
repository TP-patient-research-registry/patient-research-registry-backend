from .base import *  # noqa: F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

# TLS terminates at nginx, which sets X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# HTTP→HTTPS redirect is done by nginx. Not enabled here because the frontend container calls
# http://backend:8000/api/auth/session over the internal network.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.Argon2PasswordHasher"]

ADMINS = [("Admin", email) for email in env.list("ADMIN_EMAILS", default=[])]

SILENCED_SYSTEM_CHECKS = [
    "security.W008",  # SSL redirect is done by nginx (see SECURE_SSL_REDIRECT above)
    "security.W021",  # HSTS preload is an explicit opt-in via SECURE_HSTS_PRELOAD
]
