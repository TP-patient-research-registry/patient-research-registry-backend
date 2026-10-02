#!/bin/sh
set -e

# Only the `backend` service sets these (celery containers must not race on migrations).
if [ "${DJANGO_MIGRATE:-0}" = "1" ]; then
    python manage.py migrate --noinput
fi
if [ "${DJANGO_COLLECTSTATIC:-0}" = "1" ]; then
    python manage.py collectstatic --noinput --verbosity 0
fi

exec "$@"
