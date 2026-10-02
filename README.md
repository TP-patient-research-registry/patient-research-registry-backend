# Patient Research Registry — Backend

REST API connecting patients and volunteers with clinical research studies in Slovakia.
Participants keep a health profile, manage consents and join studies. Researchers publish studies,
collect questionnaire answers and see participants only under per-study pseudonyms.

The frontend is a separate Next.js app (`patient-research-registry-frontend`). In production both
run behind one nginx on the same origin, so authentication is a plain Django session cookie.

> Health data is special-category data under **GDPR art. 9**. Read [Security & GDPR](#security--gdpr)
> before changing models, logging or emails.

## Stack

| Concern        | Choice                                                                        |
| -------------- | ----------------------------------------------------------------------------- |
| Runtime        | Python 3.12, [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`)  |
| Framework      | Django 5.2 LTS, Django REST Framework, drf-spectacular (OpenAPI 3)           |
| Auth           | django-allauth **headless** (email login, mandatory email verification, TOTP 2FA), session cookies only, no JWT |
| Authorization  | Role per user + django-guardian object permissions on studies; default deny |
| Data security  | django-cryptography (field encryption), django-auditlog, argon2 passwords    |
| Async          | Celery + Redis                                                               |
| Database       | PostgreSQL 16 (psycopg 3)                                                    |
| Quality        | pytest-django, factory-boy, ruff, pre-commit                                 |
| Delivery       | Docker (multi-stage, non-root, gunicorn), GitHub Actions → `ghcr.io`         |

## Getting started

Requirements: [uv](https://docs.astral.sh/uv/getting-started/installation/), Docker (for PostgreSQL + Redis).

```bash
uv sync                      # creates .venv with Python 3.12 + all dependencies
cp .env.example .env         # optional for dev: config/settings/dev.py has local defaults
make deps                    # PostgreSQL 16 + Redis via deploy/docker-compose.dev.yml
make migrate
make seed                    # fake demo data (researcher@demo.example / participant1@demo.example)
make superuser
make dev                     # http://localhost:8000
```

When running the dev server with the Next.js frontend (`pnpm dev`), set
`API_INTERNAL_URL=http://localhost:8000` in the frontend. Its proxy forwards `/api/*` here.

### Make targets

| Target           | Description                                             |
| ---------------- | ------------------------------------------------------- |
| `make dev`       | Start Postgres/Redis and the Django dev server          |
| `make worker`    | Run a Celery worker locally                             |
| `make migrate`   | Apply migrations (`make migrations` to create them)     |
| `make test`      | Run pytest                                              |
| `make lint`      | Ruff lint + format check + missing-migration check      |
| `make format`    | Ruff autofix + format                                   |
| `make schema`    | Export and validate the OpenAPI schema to `schema.yml`  |
| `make superuser` | Create an admin account                                 |
| `make seed`      | `python manage.py seed_demo` (fake data, refuses to run when `DEBUG=False` unless `--force`) |

Install the git hooks once: `uv run pre-commit install`.

## API

| URL                              | Description                                                        |
| -------------------------------- | ------------------------------------------------------------------ |
| `/api/docs/`                     | Swagger UI                                                         |
| `/api/schema/`                   | OpenAPI schema. Paths are relative to `/api` (used by the frontend's `pnpm gen:api`) |
| `/api/auth/openapi.html`         | django-allauth headless API docs (login, signup, email verification, MFA) |
| `/admin/`                        | Django admin                                                       |

| Area                    | Who                         | Endpoints                                                                    |
| ----------------------- | --------------------------- | ---------------------------------------------------------------------------- |
| `/api/auth/browser/v1/…`| anyone                      | allauth headless: login, logout, signup (`role`: participant/researcher), email verification, password reset, TOTP |
| `/api/auth/session`     | anyone                      | `{is_authenticated, user: {id, email, role, …} \| null}`. Used by the frontend route guard; also sets the `csrftoken` cookie |
| `/api/studies/`         | anyone                      | Published studies (`?search=`)                                               |
| `/api/participant/…`    | role `participant`          | `profile/`, `consent-documents/`, `consents/` (+`withdraw`), `studies/` (+`recommended`, `apply`), `enrollments/` (+`withdraw`), `questionnaires/` (+`response`), `notification-preferences/`, `my-data/export/`, `my-data/deletion-requests/`, `my-data/access-log/` |
| `/api/researcher/…`     | role `researcher` / `organization` | `profile/`, `studies/` CRUD (+`publish`, `close`, `criteria`), `studies/{id}/participants/`, `studies/{id}/questionnaires/` (+`responses`) |
| `/api/health/`          | anyone                      | Health check for Docker                                                      |

Authentication: session cookie. Unsafe requests need the `X-CSRFToken` header containing the
`csrftoken` cookie value. Errors use one envelope:
`{"error": {"status", "code", "detail", "fields"}}`.

## Security & GDPR

- **Default deny.** `DEFAULT_PERMISSION_CLASSES = DenyAll`, so every view declares its own
  permissions. A test (`apps/core/tests/test_permissions.py`) fails if a view doesn't, or if a view
  is public without being on the allowlist.
- **Encryption at rest.** `ParticipantProfile.birth_year/sex/region/diagnoses` and questionnaire
  answers (`Response.data`) are encrypted with `FIELD_ENCRYPTION_KEY`. That key is separate from
  `SECRET_KEY` and must never be lost. Encrypted fields can't be queried in SQL, so study matching
  runs in Python (`apps/studies/services.py`).
- **Pseudonymisation.** Researchers see participants only as `Enrollment.pseudonym`, a random UUID
  generated per study. It can't be linked across studies and is never a name, email or user ID.
- **Audit log.** All sensitive models are registered with django-auditlog. Health fields are
  masked as `***`. Researchers reading questionnaire answers create `ACCESS` entries. Participants
  can see the log for their own data at `/api/participant/my-data/access-log/` (staff appear by
  role only).
- **Consents** are append-only: rows can't be edited or deleted, a withdrawal only sets
  `withdrawn_at`, and granting again creates a new row. Published consent texts are frozen. Joining
  a study requires active consent to health data processing. Matching-study emails require separate
  contact consent.
- **Emails carry no health data**, not even the study title, only a link to log in.
- **Data subject rights.** JSON export (art. 15/20). Deletion requests (art. 17) are processed by
  an admin.
- **Prod settings.** HSTS, secure + SameSite=Lax cookies, `SECURE_PROXY_SSL_HEADER`, argon2,
  `DEBUG=False`, hosts and origins from env. Gunicorn access logs omit query strings.

## Project structure

```
config/
  settings/base.py dev.py prod.py test.py
  urls.py celery.py wsgi.py asgi.py
apps/
  core/            BaseModel (UUID pk + timestamps), permissions, pagination, exception handler,
                   UUID router, health check, seed_demo command
  accounts/        User (email login, role), ParticipantProfile (encrypted), ResearcherProfile,
                   Organization, session endpoint, signup form
  consents/        ConsentDocument (versioned), Consent (immutable history)
  studies/         Study, EligibilityCriteria, Enrollment (pseudonym), matching, guardian perms
  questionnaires/  Questionnaire (SurveyJS schema), Response (encrypted answers)
  notifications/   NotificationPreference, Celery task emailing matching participants
  gdpr/            DeletionRequest, data export, access log
  <each app>/      models, serializers, views, urls, admin, permissions, services, tests/
deploy/
  docker-compose.yml       production stack (nginx, frontend, backend, celery, postgres, redis)
  docker-compose.dev.yml   postgres + redis for local development
  nginx/default.conf       reverse proxy, TLS, security headers
  backup.sh                pg_dump + restic
  README.md                server setup (Ubuntu, Docker, certbot, ufw)
Dockerfile, docker-entrypoint.sh, gunicorn.conf.py, Makefile, .env.example
```

## Deployment

See [deploy/README.md](deploy/README.md). CI (`.github/workflows/ci.yml`) runs ruff, a
missing-migrations check, pytest against PostgreSQL 16 and OpenAPI validation. On `main` it also
builds and pushes `ghcr.io/<owner>/<repo>`.
