# Rezept-Tagebuch App

Eine Flask-basierte Web-App zum Verwalten von Rezepten und Tagebucheinträgen.

**Version:** v25.11.04
**Stand:** November 2025

---

## 🚀 Schnellstart

### Zugriff auf die Apps

**PRODUCTION:**
```
http://192.168.2.139:8000/rezept-tagebuch/
```

**DEVELOPMENT:**
```
http://192.168.2.139:8000/rezept-tagebuch-dev/
```

**Authentifizierung:**
- Kein Passwort im LAN (192.168.2.x) und VPN (Tailscale)
- Passwort erforderlich bei externem Zugriff

---

## 📦 Container-Architektur

### Container-Setup

```
┌─────────────────────────────────────────────┐
│  Nginx Proxy (seaser-proxy)                │
│  Port 8000 (HTTP), 8443/8444 (HTTPS)      │
└─────────────┬──────────────────┬────────────┘
              │                  │
    /rezept-tagebuch/    /rezept-tagebuch-dev/
              │                  │
              ▼                  ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ PROD Container  │  │ DEV Container   │
    │ Port: intern    │  │ Port: intern    │
    └────────┬────────┘  └────────┬────────┘
             │                    │
             ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ Prod Database   │  │ Dev Database    │
    │ ./data/prod/    │  │ ./data/dev/     │
    └─────────────────┘  └─────────────────┘
```

### Volumes (Datenbanken) - PostgreSQL

| Environment | App Container Volume | PostgreSQL Container | Database |
|-------------|---------------------|----------------------|----------|
| **PROD**    | `/home/gabor/easer_projekte/rezept-tagebuch/data/prod` | `seaser-postgres` → `rezepte` | PostgreSQL |
| **DEV**     | `/home/gabor/easer_projekte/rezept-tagebuch/data/dev` | `seaser-postgres-dev` → `rezepte_dev` | PostgreSQL |
| **TEST**    | `/home/gabor/easer_projekte/rezept-tagebuch/data/test` | `seaser-postgres-test` → `rezepte_test` | PostgreSQL |

**Wichtig:** Komplett getrennte PostgreSQL-Datenbanken = sicheres Testen ohne Risiko für Prod-Daten!

### Container-Namen

| Environment | Container Name                 | Image Tag      |
|-------------|--------------------------------|----------------|
| **DEV**     | `seaser-rezept-tagebuch-dev`   | `:dev`         |
| **PROD**    | `seaser-rezept-tagebuch`       | `:latest`      |

---

## 🛠️ Entwicklungs-Workflow

### 1. In Dev entwickeln & testen

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Code ändern (app.py, index.html, etc.)
vim app.py

# Dev-Container neu bauen und starten
./scripts/deployment/build-dev.sh

# Testen auf: http://192.168.2.139:8000/rezept-tagebuch-dev/
```

### 2. Auf Prod deployen

```bash
# Git-Tag erstellen (automatisch mit heutigem Datum)
./scripts/tools/tag-version.sh

# Mit Git-Tag deployen
./scripts/deployment/deploy-prod.sh rezept_version_06_11_2025_001

# Prod-App ist nun auf: http://192.168.2.139:8000/rezept-tagebuch/
```

**Hinweis:** Seit Version v05.11.2025 werden nur noch Git-Tags deployed. Siehe **docs/GIT-TAG-WORKFLOW.md** für Details.

### 3. Rollback bei Problemen

```bash
# Verfügbare Git-Tags anzeigen
git tag | grep rezept_version

# Zurück zu alter Version
./scripts/deployment/rollback.sh rezept_version_05_11_2025_001
```

---

## 📝 Scripts

### Daily Import

#### daily-import.sh

Flexibler Wrapper für täglichen Rezept-Import mit Retry-Logik.

```bash
./scripts/daily-import.sh [strategy] [value]
```

**Features:**
- Retry-Logik: Bis zu 10 Versuche bei Meat-Rejection
- Parametrierbar: Verschiedene Import-Strategien
- Meat-Filter: Akzeptiert nur fleischfreie Rezepte
- Logging: Ausgabe in systemd journal

**Beispiele:**
```bash
# Vegetarisches Rezept (Standard)
./scripts/daily-import.sh by_category Vegetarian

# Italienisches Rezept
./scripts/daily-import.sh by_area Italian

# Zufälliges Rezept (mit automatischer Ablehnung von Fleisch)
./scripts/daily-import.sh random

# Dessert
./scripts/daily-import.sh by_category Dessert
```

**Was passiert:**
1. Script ruft `/api/recipes/daily-import` auf
2. Bei Ablehnung (HTTP 400 wegen Fleisch): Retry nach 2 Sekunden
3. Bis zu 10 Versuche
4. Bei Erfolg: Cleanup alter Imports
5. Logs erscheinen in systemd journal

**Siehe auch:**
- `systemd/README.md` - Systemd Service Konfiguration
- `docs/THEMEALDB-CONFIG.md` - Import-Strategien und API

### Deployment Scripts

#### build-dev.sh

Baut Dev-Image und startet Dev-Container neu.

```bash
./scripts/deployment/build-dev.sh
```

**Was passiert:**
1. Baut Image `seaser-rezept-tagebuch:dev`
2. Stoppt alten Dev-Container
3. Startet neuen Dev-Container mit Dev-Datenbank

#### test-migration.sh

Testet Datenbank-Migration auf TEST-Umgebung mit automatischen Tests.

```bash
./scripts/database/test-migration.sh
```

**Was passiert:**
1. Baut TEST Container
2. Startet TEST Container
3. Führt Alembic Migration auf TEST DB aus
4. Führt automatische Tests aus (pytest)
5. Fragt nach DEV Update (optional)

**Workflow:** TEST → DEV → TAG → PROD

Siehe **docs/MIGRATION_WORKFLOW.md** für Details.

### deploy-prod.sh

Deployed Git-Tag auf Production mit automatischer Datenbank-Migration.

```bash
./scripts/deployment/deploy-prod.sh <GIT_TAG>

# Beispiel:
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_001
```

**Was passiert:**
1. Prüft Git-Tag Existenz
2. Exportiert Git-Tag in temp-Directory
3. **Erstellt automatisches Datenbank-Backup**
4. Baut Image aus Git-Tag (z.B. `rezept_version_09_11_2025_001`)
5. Tagged Image als `:latest`
6. **Führt Alembic Migration auf PROD DB aus** (automatisch)
7. Stoppt alten Prod-Container
8. Startet neuen Prod-Container mit Prod-Datenbank
9. Aktualisiert systemd Service

### rollback.sh

Rollback zu vorheriger Version.

```bash
./scripts/deployment/rollback.sh <GIT_TAG>

# Beispiel:
./scripts/deployment/rollback.sh rezept_version_05_11_2025_001
```

**Was passiert:**
1. Prüft ob Git-Tag existiert
2. Tagged alte Version als `:latest`
3. Startet Prod-Container mit alter Version neu

### Test-Scripts

#### test-deepl.sh

Testet DeepL API Integration.

```bash
./scripts/testing/test-deepl.sh
```

**Was wird getestet:**
- DeepL API Key Validierung
- Übersetzung von Englisch nach Deutsch

#### test-recipe-import-e2e.sh

End-to-End Test für den Recipe Import Flow.

```bash
./scripts/testing/test-recipe-import-e2e.sh
```

**Was wird getestet:**
1. Dev-Container Status
2. DeepL API Konfiguration
3. TheMealDB API Import
4. DeepL Translation
5. SCHRITT Formatting
6. Zutaten Section
7. DB Storage
8. API Endpoint
9. Parser Config

#### run-tests.sh (pytest Test-Suite)

Automatisierte CRUD Tests für Recipe & Diary API (**27 Tests**).

```bash
./scripts/testing/run-tests.sh
```

**Empfohlen**: Isolierte Test-Datenbank nutzen:
```bash
./scripts/testing/run-tests-isolated.sh
```

**Was wird getestet:**
- Recipe CRUD (14 Tests)
- Diary Entry CRUD (13 Tests)
- Search Funktionalität
- Parser Integration
- Image Upload
- API Validierung

**Beispiele:**
```bash
# Nur Recipe Tests
./scripts/testing/run-tests.sh tests/test_recipes_crud.py

# Einzelner Test
./scripts/testing/run-tests.sh -k test_create_recipe

# Verbose Output
./scripts/testing/run-tests.sh -v

# Mit isolierter Test-DB
./scripts/testing/run-tests-isolated.sh -v
```

**Test-Container Lifecycle (On-Demand):**

Der Test-Container startet **automatisch** wenn pytest läuft und stoppt danach wieder:

```bash
# Container ist gestoppt
$ podman ps | grep test
# (keine Ausgabe)

# Tests laufen → Container startet automatisch
$ pytest tests/
🚀 Starting test container seaser-rezept-tagebuch-test...
✅ 27 passed in 15.70s
🧹 Stopping test container...

# Container ist wieder gestoppt
```

**Für Debugging:** Starte Container manuell - pytest stoppt ihn dann NICHT:
```bash
./scripts/deployment/build-test.sh
pytest tests/  # Container bleibt laufen
```

**Hinweis**: Tests laufen parallel mit pytest-xdist (33% schneller). PostgreSQL hat keine Lock-Probleme!

Siehe `tests/README.md` für Details.

### Git Pre-Commit Hook

Automatisch Tests vor jedem Commit ausführen:

```bash
./scripts/setup/install-git-hooks.sh
```

**Was passiert:**
- Pytest läuft automatisch vor jedem Commit
- Commit wird blockiert wenn Tests fehlschlagen
- Hook kann übersprungen werden: `git commit --no-verify`

**Hook ist bereits installiert!** Der Pre-Commit Hook ist bereits aktiv.

---

## 🐳 Container-Management

### Container Status prüfen

```bash
# Beide Container anzeigen
podman ps | grep rezept-tagebuch

# Logs ansehen
podman logs --tail 20 seaser-rezept-tagebuch      # PROD
podman logs --tail 20 seaser-rezept-tagebuch-dev  # DEV
```

### Container manuell starten/stoppen

```bash
# DEV
podman stop seaser-rezept-tagebuch-dev
podman start seaser-rezept-tagebuch-dev

# PROD
podman stop seaser-rezept-tagebuch
podman start seaser-rezept-tagebuch
```

### Systemd Services

```bash
# Status prüfen
systemctl --user status container-seaser-rezept-tagebuch.service      # PROD
systemctl --user status container-seaser-rezept-tagebuch-dev.service  # DEV

# Neu starten
systemctl --user restart container-seaser-rezept-tagebuch.service
systemctl --user restart container-seaser-rezept-tagebuch-dev.service
```

---

## 🗄️ Datenbank-Zugriff (PostgreSQL)

### Prod-Datenbank

```bash
# psql Shell öffnen
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Backup erstellen
podman exec seaser-postgres pg_dump -U postgres rezepte > backup-prod.sql
```

### Dev-Datenbank

```bash
# psql Shell öffnen
podman exec -it seaser-postgres-dev psql -U postgres -d rezepte_dev

# Dev-Datenbank zurücksetzen (sauberer Start)
podman exec seaser-postgres-dev psql -U postgres -c "DROP DATABASE rezepte_dev;"
podman exec seaser-postgres-dev psql -U postgres -c "CREATE DATABASE rezepte_dev;"
podman exec -i seaser-postgres-dev psql -U postgres -d rezepte_dev < scripts/database/schema-postgres.sql
```

### Test-Datenbank

```bash
# psql Shell öffnen
podman exec -it seaser-postgres-test psql -U postgres -d rezepte_test
```

**Hinweis:** Alle PostgreSQL Container haben separate Datenbanken - komplett isoliert!

---

## 📚 Dokumentation

- **README.md** - Dieses Dokument (Übersicht & Workflows)
- **docs/DEPLOYMENT.md** - Detaillierte Deployment-Anleitung
- **docs/MIGRATION_WORKFLOW.md** - **Alembic Migration Workflow (TEST → DEV → PROD)**
- **docs/POSTGRESQL-MIGRATION.md** - PostgreSQL Migration (100% Complete)
- **docs/MIGRATIONS.md** - Datenbank-Migrationen (Alembic)
- **docs/PROJECT-STRUCTURE.md** - Projektstruktur und Architektur
- **docs/GIT-TAG-WORKFLOW.md** - Git-Tag basierter Deployment-Workflow
- **docs/UX-GUIDE.md** - Design-Richtlinien und Best Practices
- **docs/THEMEALDB-CONFIG.md** - TheMealDB Import Konfiguration (Strategien, Filter, API)
- **docs/RECIPE-IMPORT-PROCESS.md** - BPMN Prozess-Dokumentation für Recipe Import
- **docs/RECIPE-PARSER-README.md** - Recipe Parser Konfiguration
- **docs/SEARCH-PANEL.md** - Search Panel Dokumentation
- **docs/DEEPL-TRANSLATION.md** - DeepL API Integration
- **docs/CHANGELOG.md** - Versions-Historie

---

## 🔧 Technologie-Stack

- **Backend:** Python Flask + SQLAlchemy ORM
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Datenbank:** PostgreSQL 16 (3 separate Datenbanken)
- **Migrations:** Alembic (automatisch in Deployment-Pipeline)
- **Container:** Podman
- **Proxy:** Nginx
- **Services:** systemd (user services)
- **Testing:** pytest + pytest-xdist (parallele Tests)

---

## 🎨 UX-Richtlinien

Siehe **docs/UX-GUIDE.md** für:
- CSS-Regeln und Best Practices
- CRUD-Pattern
- Design-System
- Entwicklungs-Workflow

---

## 📞 Troubleshooting

### Dev-App lädt nicht

```bash
# Container-Logs prüfen
podman logs seaser-rezept-tagebuch-dev

# Container neu starten
./scripts/deployment/build-dev.sh
```

### Prod-App lädt nicht

```bash
# Container-Logs prüfen
podman logs seaser-rezept-tagebuch

# Nginx-Proxy neu starten
systemctl --user restart container-seaser-proxy.service

# Container neu starten
systemctl --user restart container-seaser-rezept-tagebuch.service
```

### Nginx-Routing funktioniert nicht

```bash
# Nginx-Config prüfen
podman exec seaser-proxy nginx -t

# Nginx-Logs ansehen
podman logs seaser-proxy --tail 50
```

---

## 📄 Lizenz

Privates Projekt für den Heimgebrauch.

---

**Erstellt mit ❤️ und Podman**
