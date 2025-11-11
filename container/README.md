# Container Definitions

Podman/Docker Container-Definitionen für Rezept-Tagebuch.

---

## Containerfiles

### Containerfile
**Haupt-Containerfile** für alle Umgebungen (PROD/DEV/TEST).

**Base Image:** `python:3.11-slim`

**Was wird kopiert:**
- Python Code: `app.py`, `models.py`, `config.py`, etc.
- Frontend: `index.html`
- Config: `config/shared/` (JSON configs)
- Migrations: `migrations/`, `alembic*.ini`
- Tests: `tests/`, `pytest.ini`

**Umgebungs-Unterschiede:**
- PROD: Normale Ausführung
- DEV: `ENV DEV_MODE=true` gesetzt
- TEST: `ENV TESTING_MODE=true` gesetzt

**Verwendung:**
```bash
# DEV Build
podman build -t seaser-rezept-tagebuch:dev -f container/Containerfile .

# TEST Build
podman build -t seaser-rezept-tagebuch:test -f container/Containerfile .

# PROD Build (mit Version Tag)
podman build -t seaser-rezept-tagebuch:prod \
  --build-arg APP_VERSION=rezept_version_11_11_2025_001 \
  -f container/Containerfile .
```

---

### Containerfile.test-postgres
**Legacy Containerfile** für PostgreSQL Test-Setup.

**Status:** Wird aktuell nicht aktiv genutzt.

**Zweck:** War für isolierte PostgreSQL-Test-Umgebung gedacht.

---

## Container-Verwaltung

### PROD Container
```bash
# Deploy über Script
./scripts/prod/deploy.sh <git-tag>

# Manuell
podman run -d --name seaser-rezept-tagebuch \
  --network seaser-network \
  seaser-rezept-tagebuch:prod
```

### DEV Container
```bash
# Build & Start
./scripts/dev/build.sh

# Manuell
podman run -d --name seaser-rezept-tagebuch-dev \
  --network seaser-network \
  -e DEV_MODE=true \
  -v ./data/dev/uploads:/data/dev/uploads:Z \
  seaser-rezept-tagebuch:dev
```

### TEST Container
```bash
# Automatischer Test-Workflow
./scripts/test/test-and-approve-for-prod.sh

# Manuell (nur für Debugging)
./scripts/test/build.sh
```

---

## Port-Mapping

Container verwenden intern Port **80**, gemappt auf Host via Nginx:

- **PROD:** `http://192.168.2.139:8000/rezept-tagebuch/`
- **DEV:** `http://192.168.2.139:8000/rezept-tagebuch-dev/`
- **TEST:** `http://localhost:8001/` (on-demand only)

---

## Build-Argumente

### APP_VERSION
Git-Tag für Version-Tracking:

```bash
podman build --build-arg APP_VERSION=rezept_version_11_11_2025_001 \
  -t seaser-rezept-tagebuch:prod \
  -f container/Containerfile .
```

Wird als `ENV APP_VERSION` im Container gesetzt.

---

## Gunicorn Configuration

**Production Server:** Gunicorn (nicht Flask dev server!)

```python
CMD ["gunicorn",
     "--workers", "4",              # 4 Worker-Prozesse
     "--bind", "0.0.0.0:80",        # Port 80
     "--timeout", "300",            # 300s für lange Imports
     "--access-logfile", "-",       # Logs zu stdout
     "--error-logfile", "-",        # Errors zu stderr
     "--log-level", "info",         # Log-Level
     "app:app"]
```

**Warum 300s Timeout?** DeepL Translations können bei großen Rezepten lange dauern.

---

## Netzwerk

Alle Container laufen im **seaser-network** (Podman network):

```bash
# Netzwerk erstellen (falls nicht vorhanden)
podman network create seaser-network

# PostgreSQL Container müssen im gleichen Netzwerk sein
podman ps --filter network=seaser-network
```

---

## Volume Mounts

### Upload Directories
- PROD: `./data/uploads:/data/uploads:Z`
- DEV: `./data/dev/uploads:/data/dev/uploads:Z`
- TEST: `./data/test/uploads:/data/test/uploads:Z`

**Wichtig:** `:Z` Flag für SELinux-Kompatibilität!

---

## Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
podman logs seaser-rezept-tagebuch

# Container neu bauen
./scripts/dev/build.sh
```

### Port bereits belegt
```bash
# Alte Container stoppen
podman stop seaser-rezept-tagebuch
podman rm seaser-rezept-tagebuch
```

### Netzwerk nicht gefunden
```bash
# Netzwerk erstellen
podman network create seaser-network

# Container neu starten
podman start seaser-rezept-tagebuch
```

---

**Erstellt:** 2025-11-11
