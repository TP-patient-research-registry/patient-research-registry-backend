"""Gunicorn settings (env-overridable). Runs behind nginx on the internal Docker network."""

import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", min(multiprocessing.cpu_count() * 2 + 1, 8)))
threads = int(os.environ.get("GUNICORN_THREADS", 2))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 60))
max_requests = 1000
max_requests_jitter = 100
# Trust X-Forwarded-* from nginx; the backend port is never published outside Docker.
forwarded_allow_ips = "*"
accesslog = "-"
errorlog = "-"
# No query strings in access logs: search terms may reveal health information.
access_log_format = '%(h)s "%(m)s %(U)s %(H)s" %(s)s %(b)s %(L)ss'
# gunicorn's runtime control socket (gunicornc) isn't needed in containers and wants a writable $HOME.
control_socket_disable = True
