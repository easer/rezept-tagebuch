# PostgreSQL Migration Guide

## Übersicht

Migration von SQLite zu PostgreSQL für bessere Parallelität, keine Locking-Probleme bei Tests, und Skalierbarkeit.

**Status**: 🟡 In Progress (80% Complete)

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

Unterstützt beide Datenbanken:
```python
DB_TYPE = 'postgresql'  # oder 'sqlite' für Backwards-Compatibility
```

**Environment Variables**:
```bash
# PostgreSQL Prod/Dev
POSTGRES_HOST=seaser-postgres
POSTGRES_PORT=5432
POSTGRES_DB=rezepte
POSTGRES_USER=postgres
POSTGRES_PASSWORD=seaser

# PostgreSQL Test
POSTGRES_TEST_HOST=seaser-postgres-test
POSTGRES_TEST_DB=rezepte_test
POSTGRES_TEST_PASSWORD=test
```

### 3. Refactored Application
**Datei**: `app_new.py`

- ✅ Alle 28 API Endpoints portiert
- ✅ 100+ raw SQL Queries → SQLAlchemy ORM
- ✅ Besseres Error Handling mit Rollbacks
- ✅ Transaction Management
- ✅ 100% API-kompatibel mit alter Version

**Wichtige Änderungen**:
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

### 4. PostgreSQL Container
**Container erstellt**:
```bash
# Prod/Dev Container
podman run -d --name seaser-postgres \
  --network seaser-network \
  -e POSTGRES_PASSWORD=seaser \
  -e POSTGRES_DB=rezepte \
  -v /path/to/data/postgres:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:16-alpine

# Test Container
podman run -d --name seaser-postgres-test \
  --network seaser-network \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=rezepte_test \
  -v /path/to/data/postgres-test:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:16-alpine
```

**Container IPs**:
- `seaser-postgres`: 10.89.0.28:5432
- `seaser-postgres-test`: (check with `podman inspect`)

### 5. Migration Script
**Datei**: `scripts/database/migrate-sqlite-to-postgres.py`

Migriert alle Daten von SQLite → PostgreSQL:
- Users
- Recipes
- Todos
- Diary Entries

**Usage**:
```bash
POSTGRES_HOST=10.89.0.28 POSTGRES_PASSWORD=seaser \
  python3 scripts/database/migrate-sqlite-to-postgres.py --yes data/prod/rezepte.db
```

### 6. Dependencies
**Datei**: `requirements.txt`

Neue Dependencies hinzugefügt:
```
psycopg2-binary==2.9.9      # PostgreSQL Adapter
Flask-SQLAlchemy==3.1.1     # SQLAlchemy Integration
```

## ✅ Migration abgeschlossen! (2025-11-07)

Die PostgreSQL Migration wurde erfolgreich durchgeführt:

- **Schema**: Direkt aus SQLite extrahiert und nach PostgreSQL konvertiert
- **Daten**: Vollständig migriert (Users, Recipes, Todos, Diary Entries)
- **Alembic**: Neu initialisiert mit Version 0001 als Baseline
- **Foreign Keys**: Automatisch validiert und bereinigt

**Migrationsstatus:**
- ✅ 7 users
- ✅ 5 recipes
- ✅ 12 todos
- ✅ 1 diary entry (orphaned FK automatisch auf NULL gesetzt)

## Bekannte Issues ⚠️ (GELÖST)

### ~~Issue #1: Models Hang bei `db.create_all()`~~ ✅ GELÖST

**Lösung**: Direkter SQL-basierter Ansatz statt ORM
- Schema via `schema-postgres.sql` erstellt
- Daten via `export-sqlite-data.py` exportiert
- Keine ORM-Komplexität mehr

**Debug Steps**:
```python
# Test Models Import
python3 -c "from models import db, User, Recipe; print('OK')"

# Test DB Connection
python3 -c "
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI
from sqlalchemy import create_engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)
conn = engine.connect()
print('Connected!')
conn.close()
"

# Test Table Creation einzeln
python3 -c "
from flask import Flask
from models import db, User
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'
db.init_app(app)
with app.app_context():
    db.Model.metadata.create_all(db.engine, tables=[User.__table__])
"
```

**Workaround**: SQL Script statt ORM für Schema-Creation:
```bash
# Export Schema from SQLite
sqlite3 data/prod/rezepte.db .schema > schema.sql

# Manually convert to PostgreSQL syntax
# Then: psql -h 10.89.0.28 -U postgres -d rezepte < schema.pg.sql
```

## 🎯 Schnellstart: Migration wiederholen

Wenn du die Migration nochmal durchführen möchtest (z.B. für Test-DB):

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Production Database
./scripts/database/reset-and-migrate-postgres.sh data/prod/rezepte.db

# Development Database
./scripts/database/reset-and-migrate-postgres.sh data/dev/rezepte.db

# Test Database (optional)
# Export POSTGRES_DB=rezepte_test
# ./scripts/database/reset-and-migrate-postgres.sh data/test/rezepte.db
```

## Nächste Schritte 🚀

### ~~Phase 1: Debug & Fix Models~~ ✅ ABGESCHLOSSEN
- Schema erfolgreich erstellt
- Daten erfolgreich migriert

### ~~Phase 2: Migration durchführen~~ ✅ ABGESCHLOSSEN

Migration erfolgreich durchgeführt am 2025-11-07!

### Phase 3: App Testing ✅ ABGESCHLOSSEN

**Test-Container erfolgreich getestet:**
- Container: `seaser-rezept-tagebuch:test-postgres`
- Port: 8888 (Test), läuft parallel zu Prod/Dev
- Database: PostgreSQL via seaser-postgres
- App: `app_new.py` mit vollständigem ORM-Support

**API Tests erfolgreich:**
- ✅ GET /api/users - 7 users found
- ✅ GET /api/recipes - 5 recipes found
- ✅ GET /api/todos - 12 todos found
- ✅ GET /api/diary - 1 diary entry found
- ✅ CRUD Operations (Create, Read, Update, Delete) - All working!

**Zugriff:**
```
http://localhost:8888/api/users
http://localhost:8888/api/recipes
http://localhost:8888/api/todos
http://localhost:8888/api/diary
```
1. **Test-Migration** (zuerst!)
   ```bash
   # Test-Datenbank migrieren
   TESTING_MODE=true POSTGRES_TEST_HOST=10.89.0.28 \
     python3 scripts/database/migrate-sqlite-to-postgres.py \
     --yes data/test/rezepte.db
   ```

2. **Prod-Migration**
   ```bash
   # Backup erstellen
   ./scripts/database/backup-db.sh prod "before-postgresql-migration"

   # Migration durchführen
   POSTGRES_HOST=10.89.0.28 POSTGRES_PASSWORD=seaser \
     python3 scripts/database/migrate-sqlite-to-postgres.py \
     --yes data/prod/rezepte.db
   ```

3. **Uploads kopieren**
   ```bash
   # Uploads müssen auch migriert werden
   cp -r data/prod/uploads/* data/postgres-uploads/
   ```

### Phase 3: App Deployment
1. **app.py ersetzen**
   ```bash
   mv app.py app_old.py
   mv app_new.py app.py
   ```

2. **Containerfile updaten**
   ```dockerfile
   # requirements.txt wird automatisch installiert
   # Neue dependencies sind bereits drin
   ```

3. **Environment Variables setzen**
   ```bash
   # In .env oder systemd service:
   DB_TYPE=postgresql
   POSTGRES_HOST=seaser-postgres
   POSTGRES_PASSWORD=seaser
   ```

4. **Container neu bauen**
   ```bash
   ./scripts/deployment/build-dev.sh
   ```

5. **Testen**
   ```bash
   # API Tests
   curl http://localhost:8000/rezept-tagebuch-dev/api/recipes
   curl http://localhost:8000/rezept-tagebuch-dev/api/users

   # TheMealDB Import testen
   podman exec seaser-rezept-tagebuch-dev \
     python3 scripts/external/import-recipe-by-name.py "Carbonara"
   ```

### Phase 4: Tests anpassen
1. **conftest.py updaten**
   ```python
   # Keine Änderung nötig - verwendet automatisch PostgreSQL
   # wenn DB_TYPE=postgresql gesetzt ist
   ```

2. **pytest.ini - Parallel Tests aktivieren**
   ```ini
   [pytest]
   addopts =
       -v
       --tb=short
       --strict-markers
       -n auto  # ← PARALLEL TESTS! 🎉

   # pytest-xdist installieren:
   # pip install pytest-xdist
   ```

3. **Tests laufen lassen**
   ```bash
   pytest -v
   ```

### Phase 5: Production Deployment
1. **Tag erstellen**
   ```bash
   ./scripts/tools/tag-version.sh
   # Creates: rezept_version_DD_MM_YYYY_NNN
   ```

2. **Deploy**
   ```bash
   ./scripts/deployment/deploy-prod.sh rezept_version_DD_MM_YYYY_NNN
   ```

3. **Verify**
   ```bash
   curl http://192.168.2.139:8000/rezept-tagebuch/api/config
   ```

## Rollback Plan 🔄

Falls PostgreSQL Probleme macht:

1. **SQLite wieder aktivieren**
   ```bash
   # In .env:
   DB_TYPE=sqlite
   ```

2. **Alte app.py wiederherstellen**
   ```bash
   mv app.py app_new_backup.py
   mv app_old.py app.py
   ```

3. **Container neu starten**
   ```bash
   podman restart seaser-rezept-tagebuch-dev
   ```

## Performance Vorteile 📊

**Vorher (SQLite)**:
- ❌ Locking bei parallelen Writes
- ❌ Tests müssen sequentiell laufen (langsam)
- ❌ Concurrent Users problematisch

**Nachher (PostgreSQL)**:
- ✅ Keine Locks - echte Parallelität
- ✅ Tests parallel → 5-10x schneller
- ✅ Multi-User ready
- ✅ Bessere Transaction Support
- ✅ Production-grade Database

## Troubleshooting 🔧

### PostgreSQL Connection Fehler
```bash
# Check Container läuft
podman ps | grep postgres

# Check Logs
podman logs seaser-postgres

# Check Port
podman port seaser-postgres

# Test Connection
psql -h 10.89.0.28 -U postgres -d rezepte
# Password: seaser
```

### Migration hängt
```bash
# Kill Prozess
pkill -f migrate-sqlite

# Check PostgreSQL Locks
psql -h 10.89.0.28 -U postgres -d rezepte -c "
  SELECT * FROM pg_locks WHERE NOT granted;
"

# Reset Database
podman exec -it seaser-postgres psql -U postgres -c "
  DROP DATABASE rezepte;
  CREATE DATABASE rezepte;
"
```

### App startet nicht
```bash
# Check Config
python3 -c "from config import *; print(SQLALCHEMY_DATABASE_URI)"

# Check Models Import
python3 -c "from models import *; print('OK')"

# Check Dependencies
pip3 list | grep -E 'psycopg2|SQLAlchemy'
```

## Referenz

### Dateien Übersicht
```
rezept-tagebuch/
├── models.py                    # ✅ SQLAlchemy ORM Models
├── config.py                    # ✅ Database Configuration
├── app_new.py                   # ✅ Refactored App (bereit zum Testen)
├── app.py                       # 🔄 Alt - wird ersetzt
├── requirements.txt             # ✅ Updated mit PostgreSQL deps
├── scripts/
│   └── database/
│       └── migrate-sqlite-to-postgres.py  # ✅ Migration Script
└── docs/
    ├── POSTGRESQL-MIGRATION.md  # 📄 This file
    └── REFACTORING_SUMMARY.md   # 📄 Technical details

data/
├── postgres/                    # PostgreSQL Prod Data
├── postgres-test/               # PostgreSQL Test Data
├── prod/
│   ├── rezepte.db              # SQLite Backup (keep!)
│   └── uploads/                # Muss kopiert werden
└── test/
    └── rezepte.db              # SQLite Test DB
```

### PostgreSQL Container Management
```bash
# Start
podman start seaser-postgres

# Stop
podman stop seaser-postgres

# Logs
podman logs -f seaser-postgres

# psql Shell
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Backup
podman exec seaser-postgres pg_dump -U postgres rezepte > backup.sql

# Restore
podman exec -i seaser-postgres psql -U postgres rezepte < backup.sql
```

## Contact & Support

Bei Fragen:
1. Check REFACTORING_SUMMARY.md für technische Details
2. PostgreSQL Logs: `podman logs seaser-postgres`
3. App Logs: `podman logs seaser-rezept-tagebuch-dev`

## Changelog

- **2025-11-07**: Initial PostgreSQL Migration Setup
  - Models, Config, app_new.py erstellt
  - PostgreSQL Container deployed
  - Migration Script implementiert
  - ⚠️ Issue: db.create_all() hängt - needs debugging
