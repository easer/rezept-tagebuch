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

### Volumes (Datenbanken)

| Environment | Volume Mount                                           | Datenbank            |
|-------------|--------------------------------------------------------|----------------------|
| **DEV**     | `/home/gabor/easer_projekte/rezept-tagebuch/data/dev` | `rezepte.db`         |
| **PROD**    | `/home/gabor/easer_projekte/rezept-tagebuch/data/prod`| `rezepte.db`         |

**Wichtig:** Getrennte Datenbanken = sicheres Testen ohne Risiko für Prod-Daten!

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

### build-dev.sh

Baut Dev-Image und startet Dev-Container neu.

```bash
./scripts/deployment/build-dev.sh
```

**Was passiert:**
1. Baut Image `seaser-rezept-tagebuch:dev`
2. Stoppt alten Dev-Container
3. Startet neuen Dev-Container mit Dev-Datenbank

### deploy-prod.sh

Deployed Git-Tag auf Production.

```bash
./scripts/deployment/deploy-prod.sh <GIT_TAG>

# Beispiel:
./scripts/deployment/deploy-prod.sh rezept_version_06_11_2025_001
```

**Was passiert:**
1. Prüft Git-Tag Existenz
2. Exportiert Git-Tag in temp-Directory
3. Baut Image aus Git-Tag (z.B. `rezept_version_06_11_2025_001`)
4. Tagged Image als `:latest`
3. Stoppt alten Prod-Container
4. Startet neuen Prod-Container mit Prod-Datenbank
5. Aktualisiert systemd Service

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

**Hinweis**: Bei vollständigem Test-Run können SQLite Lock-Fehler auftreten (nur Test-Problem, nicht Production).

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

## 🗄️ Datenbank-Zugriff

### Dev-Datenbank

```bash
sqlite3 /home/gabor/easer_projekte/rezept-tagebuch/data/dev/rezepte.db
```

### Prod-Datenbank

```bash
sqlite3 /home/gabor/easer_projekte/rezept-tagebuch/data/prod/rezepte.db
```

### Backup erstellen

```bash
# Dev Backup (empfohlen: ./scripts/database/backup-db.sh dev)
./scripts/database/backup-db.sh dev

# Prod Backup (empfohlen: ./scripts/database/backup-db.sh prod)
./scripts/database/backup-db.sh prod
```

**Hinweis:** Alle Datenbanken und Uploads sind jetzt im Projektverzeichnis unter `./data/` organisiert.

---

## 📚 Dokumentation

- **README.md** - Dieses Dokument (Übersicht & Workflows)
- **docs/DEPLOYMENT.md** - Detaillierte Deployment-Anleitung
- **docs/UX-GUIDE.md** - Design-Richtlinien und Best Practices
- **docs/THEMEALDB-CONFIG.md** - TheMealDB Import Konfiguration (Strategien, Filter, API)
- **docs/RECIPE-IMPORT-PROCESS.md** - BPMN Prozess-Dokumentation für Recipe Import
- **docs/GIT-TAG-WORKFLOW.md** - Git-Tag basierter Deployment-Workflow
- **docs/MIGRATIONS.md** - Datenbank-Migrationen
- **docs/PROJECT-STRUCTURE.md** - Projektstruktur und Architektur
- **docs/RECIPE-PARSER-README.md** - Recipe Parser Konfiguration
- **docs/SEARCH-PANEL.md** - Search Panel Dokumentation
- **docs/DEEPL-TRANSLATION.md** - DeepL API Integration
- **docs/CHANGELOG.md** - Versions-Historie

---

## 🔧 Technologie-Stack

- **Backend:** Python Flask
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Datenbank:** SQLite
- **Container:** Podman
- **Proxy:** Nginx
- **Services:** systemd (user services)

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
