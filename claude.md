# Claude Context - Rezept-Tagebuch

Dieses Dokument enthält alle wichtigen technischen Referenzen für die Arbeit mit Claude Code am Rezept-Tagebuch Projekt.

---

## 🎯 Projekt-Übersicht

**Name:** Rezept-Tagebuch
**Typ:** Flask Web-Anwendung
**Zweck:** Rezeptverwaltung mit automatischem Import von TheMealDB und Migusto

**Tech Stack:**
- **Backend:** Python 3.11, Flask, SQLAlchemy
- **Database:** PostgreSQL 16
- **Container:** Podman
- **Reverse Proxy:** Nginx (seaser-proxy)
- **Web Server:** Gunicorn (4 workers, 300s timeout)
- **Migrations:** Alembic
- **Testing:** pytest

---

## 📁 Verzeichnisstruktur

```
rezept-tagebuch/
├── app.py                      # Haupt-Flask-App
├── models.py                   # SQLAlchemy Models
├── config.py                   # App Configuration
├── background_jobs.py          # Background Jobs
├── import_workers.py           # Import Workers
├── recipe_scraper.py           # Recipe Scraper
├── index.html                  # Frontend (Single-Page)
├── requirements.txt            # Python Dependencies
│
├── alembic.ini                 # Alembic Base Config
├── alembic-prod.ini           # PROD DB Config
├── alembic-test.ini           # TEST DB Config
├── pytest.ini                 # Pytest Config
├── .test-approvals            # PROD Deployment Approvals
│
├── migrations/                # Alembic Migrations
├── tests/                     # Pytest Tests
│
├── container/                 # Container Definitions
│   ├── Containerfile          # Haupt-Containerfile
│   └── Containerfile.test-postgres
│
├── config/                    # Configuration Files
│   ├── shared/               # Umgebungsunabhängig
│   │   ├── themealdb-config.json
│   │   ├── migusto-import-config.json
│   │   └── recipe-format-config.json
│   ├── prod/                 # PROD-spezifisch (leer)
│   ├── dev/                  # DEV-spezifisch (leer)
│   └── test/                 # TEST-spezifisch (leer)
│
├── scripts/                   # Management Scripts
│   ├── prod/                 # PROD Environment
│   │   ├── deploy.sh
│   │   ├── rollback.sh
│   │   ├── install-daily-import.sh
│   │   └── automation/
│   │       ├── daily-import-themealdb.sh
│   │       └── daily-import-migusto.sh
│   ├── dev/                  # DEV Environment
│   │   ├── build.sh
│   │   └── test-recipe-import-e2e.sh
│   ├── test/                 # TEST Environment
│   │   ├── build.sh
│   │   ├── test-and-approve-for-prod.sh
│   │   ├── run-tests.sh
│   │   └── run-parallel-tests.sh
│   └── shared/               # Umgebungsunabhängig
│       ├── tag-version.sh
│       ├── ki-code-review.sh
│       ├── test-deepl.sh
│       └── test-postgres-connection.py
│
├── systemd/                   # Systemd Services
│   ├── prod/                 # PROD Daily Import Services
│   │   ├── rezept-daily-import.service
│   │   ├── rezept-daily-import.timer
│   │   ├── rezept-daily-migusto-import.service
│   │   └── rezept-daily-migusto-import.timer
│   ├── dev/                  # Aktuell keine Services
│   └── test/                 # Aktuell keine Services
│
├── docs/                      # Dokumentation
└── archive/                   # Archivierte Dateien
    └── sqlite-old-20251111/  # SQLite→PostgreSQL Migration
```

---

## 🌐 Umgebungen

### PROD Environment
- **Container:** `seaser-rezept-tagebuch`
- **Image:** `localhost/seaser-rezept-tagebuch:latest`
- **Database:** `seaser-postgres` / `rezepte`
- **URL:** http://192.168.2.139:8000/rezept-tagebuch/
- **Auth:** Basic Auth (nginx.htpasswd)
- **Deployment:** Git-Tag basiert (`./scripts/prod/deploy.sh <tag>`)

### DEV Environment
- **Container:** `seaser-rezept-tagebuch-dev`
- **Image:** `localhost/seaser-rezept-tagebuch:dev`
- **Database:** `seaser-postgres-dev` / `rezepte_dev`
- **URL:** http://192.168.2.139:8000/rezept-tagebuch-dev/
- **Auth:** Basic Auth (nginx.htpasswd)
- **ENV:** `DEV_MODE=true`
- **Build:** `./scripts/dev/build.sh`

### TEST Environment
- **Container:** `seaser-rezept-tagebuch-test`
- **Image:** `localhost/seaser-rezept-tagebuch:test`
- **Database:** `seaser-postgres-test` / `rezepte_test`
- **URL:** http://localhost:8001/
- **ENV:** `TESTING_MODE=true`
- **Usage:** On-demand only (`./scripts/test/test-and-approve-for-prod.sh`)

---

## 🐳 Podman Network & Nginx

### Podman Network: seaser-network
```bash
# Network Details
Network Name: seaser-network
Network ID: ebcf74d9ea3abdc5f026d2ee5be4712a57fbd15e346856916fdbe311251fdda6
Driver: bridge
Interface: podman1
Subnet: 10.89.0.0/24
Gateway: 10.89.0.1
DNS: Enabled
```

### Container im Netzwerk
```bash
# Alle Rezept-Tagebuch Container
seaser-rezept-tagebuch          # PROD App
seaser-rezept-tagebuch-dev      # DEV App
seaser-rezept-tagebuch-test     # TEST App (on-demand)

# PostgreSQL Datenbanken
seaser-postgres                 # PROD DB (rezepte)
seaser-postgres-dev             # DEV DB (rezepte_dev)
seaser-postgres-test            # TEST DB (rezepte_test)

# Nginx Reverse Proxy
seaser-proxy                    # Port 8000 (HTTP), 8443 (HTTPS)
```

### Nginx Reverse Proxy Configuration

**Container:** `seaser-proxy`
**Ports:**
- `8000:80/tcp` (HTTP)
- `8443:443/tcp` (HTTPS)
- `8444:8444/tcp`

**Config Location:** `/etc/nginx/conf.d/default.conf`

**Rezept-Tagebuch Routes:**

```nginx
# PROD - http://192.168.2.139:8000/rezept-tagebuch/
location ~ ^/rezept-tagebuch/(.*)$ {
    auth_basic $auth_type;
    auth_basic_user_file /etc/nginx/nginx.htpasswd;

    set $backend_seaser_rezept_tagebuch "seaser-rezept-tagebuch";
    set $rezept_tagebuch_path $1;

    proxy_pass http://$backend_seaser_rezept_tagebuch:80/$rezept_tagebuch_path$is_args$args;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# DEV - http://192.168.2.139:8000/rezept-tagebuch-dev/
location ~ ^/rezept-tagebuch-dev/(.*)$ {
    auth_basic $auth_type;
    auth_basic_user_file /etc/nginx/nginx.htpasswd;

    set $backend_seaser_rezept_tagebuch_dev "seaser-rezept-tagebuch-dev";
    set $rezept_tagebuch_path $1;

    proxy_pass http://$backend_seaser_rezept_tagebuch_dev:80/$rezept_tagebuch_path$is_args$args;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Wichtig:**
- Basic Auth via `nginx.htpasswd`
- Dynamische DNS-Auflösung (verhindert IP-Caching)
- Container werden per Hostname angesprochen (DNS im seaser-network)

---

## 🗄️ Datenbank

### PostgreSQL Configuration

**PROD Database:**
```bash
Host: seaser-postgres
Port: 5432
Database: rezepte
User: postgres
Password: seaser
```

**DEV Database:**
```bash
Host: seaser-postgres-dev
Port: 5432
Database: rezepte_dev
User: postgres
Password: seaser
```

**TEST Database:**
```bash
Host: seaser-postgres-test
Port: 5432
Database: rezepte_test
User: postgres
Password: seaser
```

### Database Models (models.py)

**Tabellen:**
- `recipes` - Hauptrezepte
- `alembic_version` - Migration Tracking

**Recipe Model:**
```python
class Recipe(Base):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    ingredients = Column(Text)
    instructions = Column(Text)
    notes = Column(Text)
    url = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    import_source = Column(String(100))  # 'themealdb', 'migusto', 'manual'
    auto_import = Column(Boolean, default=False)
```

### Migrations (Alembic)

**Config Files:**
- `alembic.ini` - Basis-Config
- `alembic-prod.ini` - PROD DB Connection
- `alembic-test.ini` - TEST DB Connection

**Commands:**
```bash
# PROD Migration
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini upgrade head

# DEV Migration
podman exec seaser-rezept-tagebuch-dev alembic upgrade head

# TEST Migration
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini upgrade head

# Create new Migration
alembic revision -m "description"
```

---

## 🚀 Deployment Workflow

### Git-basierter Workflow

**1. Code-Änderungen committen**
```bash
git add .
git commit -m "Feature: xyz"
git push
```

**2. Tests & Approvals**
```bash
# Vollständiger Test-Workflow
./scripts/test/test-and-approve-for-prod.sh

# Was passiert:
# 1. Prüft Working Directory (muss clean sein)
# 2. Baut TEST Container aus HEAD (git archive)
# 3. Startet TEST Container
# 4. Führt Alembic Migrationen aus
# 5. Führt pytest Tests aus
# 6. Bei Erfolg: Commit-Hash → .test-approvals
# 7. Optional: DEV Container aktualisieren
```

**3. Git-Tag erstellen**
```bash
# Tag erstellen (nur approved commits!)
./scripts/shared/tag-version.sh

# Format: rezept_version_DD_MM_YYYY_NNN
# Beispiel: rezept_version_11_11_2025_001
```

**4. PROD Deployment**
```bash
# Deploy mit Git-Tag
./scripts/prod/deploy.sh rezept_version_11_11_2025_001

# Was passiert:
# 1. Prüft .test-approvals (nur approved tags!)
# 2. Baut Image aus Git-Tag (git archive)
# 3. DB Backup
# 4. Alembic Migration auf PROD
# 5. Container Stop/Remove/Start
# 6. Nginx Reload
# 7. Cleanup alter Images
```

**5. Bei Problemen: Rollback**
```bash
./scripts/prod/rollback.sh rezept_version_10_11_2025_003
```

---

## 🤖 Automatische Imports

### Systemd Timer (PROD)

**TheMealDB Daily Import:**
- **Service:** `rezept-daily-import.service`
- **Timer:** `rezept-daily-import.timer`
- **Schedule:** Täglich um 06:00 UTC
- **Strategy:** `by_category Vegetarian`
- **Script:** `scripts/prod/automation/daily-import-themealdb.sh`

**Migusto Daily Import:**
- **Service:** `rezept-daily-migusto-import.service`
- **Timer:** `rezept-daily-migusto-import.timer`
- **Schedule:** Täglich um 07:00 UTC
- **Preset:** `vegetarische_pasta_familie`
- **Script:** `scripts/prod/automation/daily-import-migusto.sh`

**Installation:**
```bash
# Services installieren
./scripts/prod/install-daily-import.sh

# Status prüfen
systemctl --user list-timers | grep rezept

# Logs ansehen
journalctl --user -u rezept-daily-import.service --since today
```

---

## 🧪 Testing

### Pytest Configuration

**Config:** `pytest.ini` (Root)

**Test-Suites:**
```bash
# Alle Tests
./scripts/test/run-tests.sh

# Parallel Tests
./scripts/test/run-parallel-tests.sh

# Spezifische Tests
./scripts/test/run-tests.sh -k test_api

# Mit Coverage
pytest --cov=. --cov-report=html
```

**Test-Struktur:**
```
tests/
├── conftest.py              # Fixtures
├── test_api.py             # API Tests
├── test_crud.py            # CRUD Tests
├── test_parser.py          # Parser Tests
└── test_import.py          # Import Tests
```

**Wichtig:**
- Tests laufen gegen TEST Container (Port 8001)
- PostgreSQL Database (rezepte_test)
- `TESTING_MODE=true` muss gesetzt sein

---

## 📝 Wichtige Dateien

### App-Code
- **app.py** (52KB) - Flask App mit allen Routes
- **models.py** - SQLAlchemy Models
- **config.py** - Database & Upload Configuration
- **background_jobs.py** - Background Job Management
- **import_workers.py** - Import Worker Functions
- **recipe_scraper.py** - Web Scraping Logic
- **index.html** (178KB) - Frontend Single-Page App

### Konfiguration
- **config/shared/themealdb-config.json** - TheMealDB Import-Strategien
- **config/shared/migusto-import-config.json** - Migusto Import-Presets
- **config/shared/recipe-format-config.json** - Recipe Parser Patterns

### Container
- **container/Containerfile** - Multi-Environment Containerfile
- Verwendet Gunicorn (4 workers, 300s timeout)
- Kopiert Code, Configs, Migrations, Tests

---

## 🔑 Environment Variables

**Wichtige ENV Vars:**
```bash
# Mode Detection
DEV_MODE=true              # DEV Environment
TESTING_MODE=true          # TEST Environment
# (keine ENV = PROD)

# DeepL API (optional)
DEEPL_API_KEY=xxx          # Für Übersetzungen

# PostgreSQL Connection (automatisch von config.py)
POSTGRES_HOST=seaser-postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=seaser
POSTGRES_DB=rezepte
POSTGRES_PORT=5432
```

**ENV Datei:** `.env` (nicht in Git!)

---

## 🛠️ Nützliche Commands

### Container Management
```bash
# Status
podman ps | grep rezept

# Logs
podman logs -f seaser-rezept-tagebuch
podman logs -f seaser-rezept-tagebuch-dev

# Shell
podman exec -it seaser-rezept-tagebuch bash

# Restart
podman restart seaser-rezept-tagebuch
```

### Database Management
```bash
# Backup
mkdir -p data/prod/backups
podman exec seaser-postgres pg_dump -U postgres rezepte > data/prod/backups/backup.sql

# Restore
cat backup.sql | podman exec -i seaser-postgres psql -U postgres rezepte

# Connect
podman exec -it seaser-postgres psql -U postgres -d rezepte
```

### Nginx Management
```bash
# Config testen
podman exec seaser-proxy nginx -t

# Reload
podman exec seaser-proxy nginx -s reload

# Logs
podman logs -f seaser-proxy
```

---

## 📚 Dokumentation

**Haupt-Docs:**
- `README.md` - Projekt-Übersicht
- `docs/THEMEALDB-CONFIG.md` - TheMealDB Integration
- `docs/RECIPE-IMPORT-PROCESS.md` - Import-Workflow
- `docs/RECIPE-PARSER-README.md` - Parser-Dokumentation
- `docs/PROD-STABILITY-ANALYSIS.md` - Stability Analysis
- `docs/CHANGELOG.md` - Änderungshistorie

**Script-Docs:**
- `scripts/prod/README.md` - PROD Scripts
- `scripts/dev/README.md` - DEV Scripts
- `scripts/test/README.md` - TEST Scripts
- `scripts/shared/README.md` - Shared Scripts
- `systemd/prod/README.md` - Systemd Services
- `container/README.md` - Container Details
- `config/README.md` - Configuration Details

---

## 🗄️ Archive

**Location:** `archive/sqlite-old-20251111/`

**Inhalt:**
- Alte SQLite Datenbanken (28 KB)
- SQLite Backup-Dateien (11 Stück)
- Alte App-Versionen (app_old_sqlite.py, app_new.py)
- Migration-Scripts (SQLite→PostgreSQL)
- Veraltete Database-Scripts
- Alte Config-Dateien (alembic.ini, pytest.ini)
- install-git-hooks.sh (veraltet)

**Grund:** Migration von SQLite zu PostgreSQL abgeschlossen (2025-11-11)

---

## 🚨 Wichtige Hinweise

### Security
- **Basic Auth:** Alle Umgebungen durch nginx.htpasswd geschützt
- **Keine Secrets in Git:** `.env` ist in `.gitignore`
- **DEEPL_API_KEY:** Nur in .env, nicht committen

### Deployment
- **Nur approved Commits:** `.test-approvals` Gate vor PROD
- **Git-Tag basiert:** Keine Working-Dir Deployments
- **Immer testen:** `test-and-approve-for-prod.sh` vor Deployment

### Database
- **PostgreSQL only:** Kein SQLite Support mehr
- **Migrations:** Immer über Alembic, nie manuell
- **Backups:** Automatisch vor jedem PROD Deployment

### Container
- **Netzwerk:** Alle Container in `seaser-network`
- **DNS:** Container-Namen als Hostnames nutzen
- **Volumes:** `:Z` Flag für SELinux!

---

## 📞 Troubleshooting

### Container startet nicht
```bash
# Logs prüfen
podman logs seaser-rezept-tagebuch

# Container neu bauen
./scripts/dev/build.sh  # für DEV
./scripts/prod/deploy.sh <tag>  # für PROD
```

### Database Connection Failed
```bash
# PostgreSQL läuft?
podman ps | grep seaser-postgres

# Verbindung testen
./scripts/shared/test-postgres-connection.py

# Container im gleichen Netzwerk?
podman network inspect seaser-network
```

### Nginx 502 Bad Gateway
```bash
# App-Container läuft?
podman ps | grep seaser-rezept-tagebuch

# Nginx Config testen
podman exec seaser-proxy nginx -t

# Nginx Logs
podman logs seaser-proxy | tail -50
```

### Tests schlagen fehl
```bash
# TEST Container läuft?
podman ps | grep seaser-rezept-tagebuch-test

# Port 8001 erreichbar?
curl http://localhost:8001/

# Test-Logs
podman logs seaser-rezept-tagebuch-test
```

---

**Erstellt:** 2025-11-11
**Letzte Aktualisierung:** 2025-11-11
**Version:** 1.0

**Maintainer:** Rezept-Tagebuch DevOps
