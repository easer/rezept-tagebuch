# PostgreSQL Migration - Quick Start

## TL;DR - Was ist der Status?

🟡 **80% Fertig** - Aber `db.create_all()` hängt (Models Issue)

### Was funktioniert ✅
- SQLAlchemy Models definiert (`models.py`)
- App refactored (`app_new.py`) - alle Endpoints
- PostgreSQL Container läuft
- Migration Script bereit

### Was fehlt ⚠️
- Models debuggen (hängt bei Table Creation)
- Migration testen
- app.py ersetzen

---

## Schnellstart für's Debuggen

### 1. Models Issue fixen

**Problem**: `db.create_all()` hängt

**Quick Fix Option A** - Models Import testen:
```bash
python3 -c "from models import db, User, Recipe, Todo, DiaryEntry; print('Models OK')"
```

**Quick Fix Option B** - Manuelle Table Creation:
```bash
# Connect zu PostgreSQL
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Manuell Tables anlegen (PostgreSQL Syntax):
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_color VARCHAR(7) DEFAULT '#FFB6C1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Siehe docs/POSTGRESQL-MIGRATION.md für vollständiges Schema
```

### 2. Migration durchführen (nach Fix)

```bash
# Test-Migration
POSTGRES_HOST=10.89.0.28 POSTGRES_PASSWORD=seaser \
  python3 scripts/database/migrate-sqlite-to-postgres.py --yes data/prod/rezepte.db
```

### 3. App testen

```bash
# app.py ersetzen
mv app.py app_old.py && mv app_new.py app.py

# Container neu bauen
./scripts/deployment/build-dev.sh

# Testen
curl http://localhost:8000/rezept-tagebuch-dev/api/recipes
```

---

## One-Liner Commands

```bash
# PostgreSQL Status
podman ps | grep postgres

# PostgreSQL Shell
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Check Tables
podman exec seaser-postgres psql -U postgres -d rezepte -c "\dt"

# PostgreSQL Logs
podman logs seaser-postgres

# Migration Script (mit Debug)
POSTGRES_HOST=10.89.0.28 POSTGRES_PASSWORD=seaser python3 -u \
  scripts/database/migrate-sqlite-to-postgres.py --yes data/prod/rezepte.db

# Test API
curl http://localhost:8000/rezept-tagebuch-dev/api/users | jq
```

---

## Wenn's nicht klappt → Rollback

```bash
# 1. SQLite wieder aktivieren
echo "DB_TYPE=sqlite" >> .env

# 2. Alte app.py
mv app.py app_new.py && mv app_old.py app.py

# 3. Container restart
podman restart seaser-rezept-tagebuch-dev

# 4. Testen
curl http://localhost:8000/rezept-tagebuch-dev/api/recipes
```

---

## Vollständige Docs

Siehe: `docs/POSTGRESQL-MIGRATION.md`
