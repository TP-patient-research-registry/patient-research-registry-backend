# Deployment — single Ubuntu server

Production runs as one Docker Compose stack (`deploy/docker-compose.yml`):

```
Internet ──► nginx :80/:443 ──┬─► frontend:3000   (Next.js, ghcr.io image)
                              ├─► backend:8000    (/api/, /admin/ — Django + gunicorn)
                              └─► /static/        (served from the shared `static` volume)
             backend, celery-worker, celery-beat ──► postgres, redis   (internal network, no internet)
```

Only nginx publishes ports. PostgreSQL and Redis sit on an `internal` network that has no route to
the internet.

## 1. Server preparation (Ubuntu 24.04 LTS)

```bash
# System updates + automatic security updates
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y unattended-upgrades fail2ban
sudo dpkg-reconfigure -plow unattended-upgrades

# Non-root deploy user with SSH key login; then disable password + root login in /etc/ssh/sshd_config:
#   PasswordAuthentication no
#   PermitRootLogin no
sudo adduser deploy && sudo usermod -aG sudo deploy
sudo systemctl restart ssh
```

### Firewall (ufw)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

> Docker writes its own iptables rules and **bypasses ufw for published ports**. That's why only
> nginx publishes ports in the compose file. Never add `ports:` to postgres, redis or backend.

### Docker Engine

```bash
# https://docs.docker.com/engine/install/ubuntu/
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker deploy   # log out/in afterwards
```

If the GHCR packages are private, log in with a token that has `read:packages`:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-user> --password-stdin
```

## 2. Application files

```bash
sudo mkdir -p /opt/registry && sudo chown deploy: /opt/registry
git clone <backend-repo-url> /opt/registry
cd /opt/registry/deploy
cp ../.env.example .env
chmod 600 .env
nano .env   # DOMAIN, images, SECRET_KEY, FIELD_ENCRYPTION_KEY, POSTGRES_PASSWORD (+ DATABASE_URL), EMAIL_URL, ...
```

Generate secrets with `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`.

> **FIELD_ENCRYPTION_KEY** encrypts all health data. If you lose it, that data can't be recovered.
> Store a copy offline (e.g. in a password manager or a sealed envelope) as well as in the backups.

## 3. TLS certificate (Let's Encrypt / certbot)

The DNS A/AAAA records for `DOMAIN` must point to the server.

```bash
sudo apt install -y certbot
sudo mkdir -p /var/www/certbot

# First certificate: nginx isn't running yet, so use certbot's standalone server on :80
sudo certbot certonly --standalone -d registry.example.sk --agree-tos -m admin@example.sk --no-eff-email

# Later renewals use the webroot served by nginx and reload nginx afterwards
sudo tee /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh > /dev/null <<'EOF'
#!/bin/sh
cd /opt/registry/deploy && docker compose exec nginx nginx -s reload
EOF
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
sudo sed -i 's/^authenticator = standalone/authenticator = webroot\nwebroot_path = \/var\/www\/certbot/' \
  /etc/letsencrypt/renewal/registry.example.sk.conf
sudo certbot renew --dry-run
```

certbot's systemd timer renews certificates automatically.

## 4. Start

```bash
cd /opt/registry/deploy
docker compose pull
docker compose up -d
docker compose ps                 # all services should become "healthy"
docker compose exec backend python manage.py createsuperuser
```

The `backend` container runs migrations and `collectstatic` on start (`DJANGO_MIGRATE=1`,
`DJANGO_COLLECTSTATIC=1`). The Celery containers don't.

Smoke test:

```bash
curl -I http://registry.example.sk               # 301 → https
curl https://registry.example.sk/api/health/     # {"status":"ok"}
```

## 5. Updates

CI pushes `ghcr.io/<owner>/<repo>:latest` (plus `sha-…` tags) on every push to `main`.

```bash
cd /opt/registry && git pull            # compose/nginx changes
cd deploy && docker compose pull && docker compose up -d
docker image prune -f
```

To roll back, pin `BACKEND_IMAGE` / `FRONTEND_IMAGE` in `.env` to a previous `sha-…` tag and run
`docker compose up -d`.

## 6. Backups (restic)

`backup.sh` dumps PostgreSQL (`pg_dump -Fc`) and backs up the dump together with `deploy/.env`
(which contains `FIELD_ENCRYPTION_KEY`) to an encrypted, off-site restic repository. Old snapshots
are pruned (7 daily, 4 weekly, 12 monthly).

```bash
sudo apt install -y restic
cat > /opt/registry/deploy/backup.env <<'EOF'
RESTIC_REPOSITORY=sftp:backup@backup-host:/srv/restic/registry
RESTIC_PASSWORD_FILE=/root/.restic-password
EOF
chmod 600 /opt/registry/deploy/backup.env
sudo sh -c 'python3 -c "import secrets; print(secrets.token_urlsafe(48))" > /root/.restic-password && chmod 600 /root/.restic-password'
sudo -E restic -r <repo> init --password-file /root/.restic-password

# Daily at 02:30
echo '30 2 * * * root /opt/registry/deploy/backup.sh >> /var/log/registry-backup.log 2>&1' | sudo tee /etc/cron.d/registry-backup
```

Keep the restic password somewhere other than the server. **Test a restore regularly:**

```bash
restic restore latest --target /tmp/restore
docker compose exec -T postgres pg_restore -U registry -d registry_restore_test < /tmp/restore/.../registry.dump
```

## 7. Operations checklist

- [ ] `docker compose ps` shows everything healthy.
- [ ] Logs: `docker compose logs -f backend celery-worker`. Request bodies and query strings are
      never logged.
- [ ] Researchers are verified by an admin (`/admin/` → Researcher profiles → `is_verified`).
- [ ] GDPR deletion requests are processed in `/admin/` → GDPR → Deletion requests.
- [ ] Consider restricting `/admin/` to known IPs (see `nginx/default.conf`).
- [ ] Check that backups and restores actually work (section 6).
