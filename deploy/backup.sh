#!/usr/bin/env bash
# Encrypted off-site backup: PostgreSQL dump + deploy/.env (holds FIELD_ENCRYPTION_KEY) via restic.
#
# Requires deploy/backup.env with at least:
#   RESTIC_REPOSITORY=sftp:backup@backup-host:/srv/restic/registry   (or s3:..., b2:..., rest:...)
#   RESTIC_PASSWORD_FILE=/root/.restic-password
# plus credentials for the chosen backend (e.g. AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY).
#
# Cron (daily at 02:30):  30 2 * * * /opt/registry/deploy/backup.sh >> /var/log/registry-backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")"
set -a
# shellcheck disable=SC1091
. ./backup.env
set +a
: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY not set}"

umask 077
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

echo "[$(date -Is)] dumping database"
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
    > "$workdir/registry.dump"

echo "[$(date -Is)] uploading to restic"
restic backup --tag registry --host registry "$workdir/registry.dump" ./.env

echo "[$(date -Is)] applying retention policy"
restic forget --tag registry --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune

# Weekly integrity check (Sundays) on a sample of the data.
if [ "$(date +%u)" = "7" ]; then
    restic check --read-data-subset=5%
fi

echo "[$(date -Is)] backup finished"
