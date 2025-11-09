# PostgreSQL Migration Guide

## Übersicht

Migration von SQLite zu PostgreSQL für bessere Parallelität, keine Locking-Probleme bei Tests, und Skalierbarkeit.

**Status**: ✅ Complete (100%) - Erfolgreich abgeschlossen am 2025-11-09

## 🎉 Migration erfolgreich abgeschlossen!

Die PostgreSQL-Migration wurde vollständig abgeschlossen mit:
- ✅ 3 separate PostgreSQL-Datenbanken (Production, Development, Test)
- ✅ Alle Container laufen mit PostgreSQL
- ✅ Schema direkt aus SQLite extrahiert und konvertiert
- ✅ Daten vollständig migriert
- ✅ Alembic neu initialisiert (Version 0001)
- ✅ Alle 27 Tests bestanden (mit paralleler Ausführung)

## Was wurde bereits implementiert ✅

### 1. SQLAlchemy ORM Models
**Datei**: `models.py`

Vollständige ORM Models für:
- `User` - Benutzer-Management
- `Recipe` - Rezepte mit Auto-Import Support
- `Todo` - Todo-Listen
- `DiaryEntry` - Tagebuch-Einträge

Alle Models haben:
- Relationships definiert
- `to_dict()` Methoden für JSON-Serialisierung
- Proper Foreign Keys mit CASCADE-Verhalten

### 2. Database Configuration
**Datei**: `config.py`

Unterstützt PostgreSQL mit 3-Environment-Architektur:
```python
DB_TYPE = 'postgresql'  # Default: PostgreSQL
DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'
TESTING_MODE = os.environ.get('TESTING_MODE', 'false').lower() == 'true'
```

**3-Environment-Architektur**:

| Environment | Container | Database | PostgreSQL Server | DB Name |
|-------------|-----------|----------|-------------------|---------|
| **PROD** | `seaser-rezept-tagebuch` | `seaser-postgres` | `seaser-postgres:5432` | `rezepte` |
| **DEV** | `seaser-rezept-tagebuch-dev` | `seaser-postgres-dev` | `seaser-postgres-dev:5432` | `rezepte_dev` |
| **TEST** | Tests (pytest) | `seaser-postgres-test` | `seaser-postgres-test:5432` | `rezepte_test` |

**Environment Variables** (per Container via `-e` flags):
```bash
# Production
-e DB_TYPE=postgresql
-e POSTGRES_HOST=seaser-postgres
-e POSTGRES_DB=rezepte
-e POSTGRES_PASSWORD=seaser

# Development
-e DB_TYPE=postgresql
-e DEV_MODE=true
-e POSTGRES_HOST=seaser-postgres-dev
-e POSTGRES_DB=rezepte_dev
-e POSTGRES_PASSWORD=seaser

# Test
-e DB_TYPE=postgresql
-e TESTING_MODE=true
-e POSTGRES_HOST=seaser-postgres-test
-e POSTGRES_DB=rezepte_test
-e POSTGRES_PASSWORD=test
```

### 3. Application Deployment
**Datei**: `app.py` (ersetzt `app_new.py`)

- ✅ Alle API Endpoints auf PostgreSQL migriert
- ✅ 100+ raw SQL Queries → SQLAlchemy ORM
- ✅ Besseres Error Handling mit Rollbacks
- ✅ Transaction Management
- ✅ 100% API-kompatibel

**Deployment-Status**:
- ✅ PROD läuft mit `app.py` (PostgreSQL)
- ✅ DEV läuft mit `app.py` (PostgreSQL)
- ✅ TEST läuft mit `app.py` (PostgreSQL)
- ℹ️ Alte SQLite-Version in `app_old_sqlite.py` archiviert

**Code-Beispiel**:
```python
# ALT (sqlite3)
conn = sqlite3.connect(DATABASE)
c = conn.cursor()
c.execute('SELECT * FROM users')
users = [dict(row) for row in c.fetchall()]

# NEU (SQLAlchemy)
users = User.query.all()
users_dict = [user.to_dict() for user in users]
```

### 4. PostgreSQL Container (3-Environment-Setup)
**Alle Container erstellt und laufen**:
```bash
# Production Database
podman run -d --name seaser-postgres \
  --network seaser-network \
  -e POSTGRES_PASSWORD=seaser \
  -e POSTGRES_DB=rezepte \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/postgres-prod:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:16-alpine

# Development Database
podman run -d --name seaser-postgres-dev \
  --network seaser-network \
  -e POSTGRES_PASSWORD=seaser \
  -e POSTGRES_DB=rezepte_dev \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/postgres-dev:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:16-alpine

# Test Database
podman run -d --name seaser-postgres-test \
  --network seaser-network \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=rezepte_test \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/postgres-test:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:16-alpine
```

**Status**: ✅ Alle Container laufen
**Network**: `seaser-network` (Podman DNS-basierte Kommunikation)

### 5. Migration Script (Schema + Daten)
**Dateien**:
- `scripts/database/schema-postgres.sql` - PostgreSQL Schema
- `scripts/database/export-sqlite-data.py` - Daten-Export mit Typ-Konvertierung

**Migration-Ansatz**: Direkter SQL-basierter Ansatz (statt ORM)

**Schema-Konvertierung**:
- SQLite `INTEGER PRIMARY KEY AUTOINCREMENT` → PostgreSQL `SERIAL PRIMARY KEY`
- SQLite `0/1` (boolean) → PostgreSQL `true/false`
- Foreign Key Constraints mit CASCADE
- Orphaned FKs automatisch auf NULL gesetzt

**Daten-Migration**:
```bash
# 1. Schema erstellen
podman exec -i seaser-postgres psql -U postgres -d rezepte < scripts/database/schema-postgres.sql

# 2. Daten exportieren und importieren
python3 scripts/database/export-sqlite-data.py data/prod/rezepte.db | \
  podman exec -i seaser-postgres psql -U postgres -d rezepte
```

### 6. Dependencies
**Datei**: `requirements.txt`

Neue Dependencies hinzugefügt:
```
psycopg2-binary==2.9.9      # PostgreSQL Adapter
Flask-SQLAlchemy==3.1.1     # SQLAlchemy Integration
pytest-xdist==3.5.0         # Parallele Tests (33% schneller)
```

## ✅ Migration abgeschlossen! (2025-11-09)

Die PostgreSQL Migration wurde erfolgreich durchgeführt:

- **3 Environments**: Production, Development, Test - alle isoliert
- **Schema**: Direkt aus SQLite extrahiert und nach PostgreSQL konvertiert
- **Daten**: Vollständig migriert (Users, Recipes, Todos, Diary Entries)
- **Alembic**: Neu initialisiert mit Version 0001 als Baseline
- **Foreign Keys**: Automatisch validiert und bereinigt (orphaned FKs → NULL)
- **Tests**: Alle 27 Tests bestanden (pytest mit paralleler Ausführung)

**Finale Datenbank-Zustände** (2025-11-09):
- ✅ **PROD**: 3 users, 7 recipes, 11 todos, 1 diary entry (testdaten entfernt)
- ✅ **DEV**: Sauber (0 recipes, 0 diary entries, 2 default users, 6 default todos)
- ✅ **TEST**: Isoliert für automatisierte Tests

## Bekannte Issues ⚠️ (ALLE GELÖST)

### ~~Issue #1: Models Hang bei `db.create_all()`~~ ✅ GELÖST

**Lösung**: Direkter SQL-basierter Ansatz statt ORM
- Schema via `schema-postgres.sql` erstellt
- Daten via `export-sqlite-data.py` exportiert
- Keine ORM-Komplexität mehr

### ~~Issue #2: Environment Variables nicht angewendet~~ ✅ GELÖST

**Problem**: Container zeigten `DEV_MODE=False` trotz `-e DEV_MODE=true`

**Root Cause**: systemd service `container-seaser-rezept-tagebuch-dev.service` startete Container automatisch mit alter Konfiguration

**Lösung**:
```bash
systemctl --user stop container-seaser-rezept-tagebuch-dev.service
systemctl --user disable container-seaser-rezept-tagebuch-dev.service
```

Danach funktionierten `-e` flags perfekt. DEV-Container braucht keinen systemd service.

### ~~Issue #3: Boolean Type Conversion~~ ✅ GELÖST

**Problem**: SQLite speichert Booleans als 0/1, PostgreSQL erwartet true/false

**Lösung**: `export-sqlite-data.py` erkennt Boolean-Spalten und konvertiert automatisch:
```python
elif column_type == 'boolean':
    return 'true' if val else 'false'
```

### ~~Issue #4: Orphaned Foreign Keys~~ ✅ GELÖST

**Problem**: diary_entry referenzierte gelöschtes recipe (FK violation)

**Lösung**: LEFT JOIN Validierung im Export-Query setzt orphaned FKs auf NULL:
```python
CASE WHEN r.id IS NULL THEN NULL ELSE d.recipe_id END as recipe_id
```

## 🔄 3-Environment-Architektur

Die Migration wurde mit **kompletter Isolierung** der 3 Environments durchgeführt:

| Environment | App Container | DB Container | Database | URL |
|-------------|--------------|--------------|----------|-----|
| **PROD** | `seaser-rezept-tagebuch` | `seaser-postgres` | `rezepte` | `/rezept-tagebuch/` |
| **DEV** | `seaser-rezept-tagebuch-dev` | `seaser-postgres-dev` | `rezepte_dev` | `/rezept-tagebuch-dev/` |
| **TEST** | pytest (Container) | `seaser-postgres-test` | `rezepte_test` | Tests nur |

**Wichtig**: Jedes Environment hat:
- ✅ Eigenen PostgreSQL Container
- ✅ Eigene Datenbank
- ✅ Eigene Environment Variables (-e flags)
- ✅ Keine Interferenz mit anderen Environments

## 🎯 Deployment-Scripts

Alle Deployment-Scripts wurden aktualisiert für PostgreSQL:

### Production
```bash
# Deployen mit Git-Tag
./scripts/deployment/deploy-prod.sh rezept_version_DD_MM_YYYY_NNN
```

**Was passiert**:
- Automatisches PostgreSQL Backup (pg_dump)
- Image Build mit PostgreSQL Config
- Container-Start mit `-e` Environment Variables
- Verbindung zu `seaser-postgres:rezepte`

### Development
```bash
# Dev-Container neu bauen und starten
./scripts/deployment/build-dev.sh
```

**Was passiert**:
- Container-Start mit `-e DEV_MODE=true`
- Verbindung zu `seaser-postgres-dev:rezepte_dev`
- Kein systemd service (manuell gemanagt)

### Test
```bash
# Tests laufen (parallel)
./scripts/testing/run-tests-isolated.sh
```

**Was passiert**:
- Container-Start mit `-e TESTING_MODE=true`
- Verbindung zu `seaser-postgres-test:rezepte_test`
- Parallele Test-Ausführung (pytest-xdist)

## Performance Vorteile 📊

**Vorher (SQLite)**:
- ❌ Locking bei parallelen Writes
- ❌ Tests sequentiell (langsam)
- ❌ Concurrent Users problematisch
- ❌ 1 Datenbank für Dev & Test (keine Isolation)

**Nachher (PostgreSQL)**:
- ✅ Keine Locks - echte Parallelität (MVCC)
- ✅ Tests parallel → **33% schneller** (pytest-xdist)
- ✅ Multi-User ready
- ✅ Bessere Transaction Support
- ✅ Production-grade Database
- ✅ **3 separate Datenbanken** - komplette Isolation
- ✅ PROD/DEV/TEST können nicht interferieren

## Troubleshooting 🔧

### PostgreSQL Connection Fehler
```bash
# Check Container läuft
podman ps | grep postgres

# Check Logs
podman logs seaser-postgres

# Test Connection (Prod)
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Test Connection (Dev)
podman exec -it seaser-postgres-dev psql -U postgres -d rezepte_dev

# Test Connection (Test)
podman exec -it seaser-postgres-test psql -U postgres -d rezepte_test
```

### Container zeigt falsche Database
```bash
# Check Environment Variables
podman inspect seaser-rezept-tagebuch-dev | grep -A 10 Env

# Sollte enthalten:
# "DEV_MODE=true"
# "POSTGRES_HOST=seaser-postgres-dev"
# "POSTGRES_DB=rezepte_dev"
```

### App startet nicht
```bash
# Check Config
python3 -c "from config import get_database_url; print(get_database_url())"

# Check Models Import
python3 -c "from models import *; print('OK')"

# Check Dependencies
pip3 list | grep -E 'psycopg2|SQLAlchemy'

# Container Logs
podman logs seaser-rezept-tagebuch-dev --tail 50
```

## Referenz

### Dateien Übersicht
```
rezept-tagebuch/
├── models.py                    # ✅ SQLAlchemy ORM Models
├── config.py                    # ✅ 3-Environment Database Configuration
├── app.py                       # ✅ PostgreSQL App (live in production)
├── app_old_sqlite.py            # 📦 SQLite Backup (archiviert)
├── requirements.txt             # ✅ PostgreSQL deps (psycopg2, pytest-xdist)
├── scripts/
│   ├── database/
│   │   ├── schema-postgres.sql        # ✅ PostgreSQL Schema
│   │   └── export-sqlite-data.py      # ✅ Daten-Export mit Typ-Konvertierung
│   ├── deployment/
│   │   ├── deploy-prod.sh             # ✅ PostgreSQL Prod Deployment
│   │   ├── build-dev.sh               # ✅ PostgreSQL Dev Build
│   │   └── build-test.sh              # ✅ PostgreSQL Test Build
└── docs/
    ├── POSTGRESQL-MIGRATION.md  # 📄 Diese Datei
    └── README.md                # 📄 Hauptdokumentation

data/
├── postgres-prod/               # PostgreSQL Prod Data
├── postgres-dev/                # PostgreSQL Dev Data
├── postgres-test/               # PostgreSQL Test Data
├── prod/                        # SQLite Backups (archiviert)
└── dev/                         # SQLite Backups (archiviert)
```

### PostgreSQL Container Management

**Production**:
```bash
# Status
podman ps | grep seaser-postgres

# Logs
podman logs -f seaser-postgres

# psql Shell
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Backup
podman exec seaser-postgres pg_dump -U postgres rezepte > backup-prod.sql

# Restore
podman exec -i seaser-postgres psql -U postgres rezepte < backup-prod.sql
```

**Development**:
```bash
# Status
podman ps | grep seaser-postgres-dev

# Logs
podman logs -f seaser-postgres-dev

# psql Shell
podman exec -it seaser-postgres-dev psql -U postgres -d rezepte_dev

# Reset Dev Database
podman exec -it seaser-postgres-dev psql -U postgres -c "DROP DATABASE rezepte_dev;"
podman exec -it seaser-postgres-dev psql -U postgres -c "CREATE DATABASE rezepte_dev;"
```

**Test**:
```bash
# Status
podman ps | grep seaser-postgres-test

# psql Shell
podman exec -it seaser-postgres-test psql -U postgres -d rezepte_test
```

## Changelog

- **2025-11-09**: Migration 100% abgeschlossen
  - ✅ 3-Environment-Architektur implementiert (PROD/DEV/TEST isoliert)
  - ✅ Alle Container laufen mit PostgreSQL
  - ✅ Alle Issues gelöst (systemd service, env vars, type conversion)
  - ✅ Tests mit paralleler Ausführung (33% schneller)
  - ✅ PROD Daten bereinigt (Testdaten entfernt)
  - ✅ DEV Datenbank sauber (fresh start)

- **2025-11-07**: Initial PostgreSQL Migration Setup
  - Models, Config, app_new.py erstellt
  - PostgreSQL Container deployed
  - Migration Script implementiert
  - Schema-Konvertierung (SQLite → PostgreSQL)
  - Daten-Migration erfolgreich
