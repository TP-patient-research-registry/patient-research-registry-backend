import os

# Convenience defaults for local development only (override in .env).
os.environ.setdefault("SECRET_KEY", "dev-insecure-secret-key")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "dev-insecure-field-encryption-key")
os.environ.setdefault("DATABASE_URL", "postgres://registry:registry@localhost:5432/registry")

from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:3000"])

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
