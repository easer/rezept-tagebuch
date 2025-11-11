# Alembic Migrations

Datenbank-Migrations für Rezept-Tagebuch mit Alembic.

---

## 📁 Struktur

```
migrations/
├── env.py                 # Alembic Environment Config
├── script.py.mako         # Template für neue Migrations
└── versions/              # Migration Scripts
    ├── 20251107_0001_postgresql_initial_schema.py
    ├── 20251109_1400_002_add_rating_to_diary.py
    ├── 20251109_1500_0003_add_happiness_to_diary.py
    └── 20251110_2100_0004_remove_happiness_from_diary.py
```

---

## 🗄️ Database Schema

### Tabellen

#### users
```sql
id              INTEGER PRIMARY KEY
email           TEXT UNIQUE NOT NULL
name            TEXT NOT NULL
avatar_color    TEXT DEFAULT '#FFB6C1'
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### recipes
```sql
id              INTEGER PRIMARY KEY
title           TEXT NOT NULL
image           TEXT
notes           TEXT
duration        FLOAT
rating          INTEGER
user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL
is_system       BOOLEAN DEFAULT false
auto_imported   BOOLEAN DEFAULT false
erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP

INDEXES:
- idx_recipes_user_id (user_id)
- idx_recipes_auto_imported (auto_imported)
```

#### diary_entries
```sql
id              INTEGER PRIMARY KEY
recipe_id       INTEGER REFERENCES recipes(id) ON DELETE SET NULL
date            DATE NOT NULL
notes           TEXT
images          TEXT
rating          INTEGER
dish_name       TEXT
user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP

INDEXES:
- idx_diary_entries_user_id (user_id)
- idx_diary_entries_recipe_id (recipe_id)
- idx_diary_entries_date (date)
```

#### todos
```sql
id              INTEGER PRIMARY KEY
text            TEXT NOT NULL
priority        INTEGER NOT NULL
completed       BOOLEAN DEFAULT false
user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP

INDEXES:
- idx_todos_user_id (user_id)
- idx_todos_completed (completed)
```

---

## 📝 Migration History

### 0001 - PostgreSQL Initial Schema (2025-11-07)
**File:** `20251107_0001_postgresql_initial_schema.py`

**Purpose:** Baseline-Migration für PostgreSQL (nach SQLite→PostgreSQL Umstellung)

**Tables Created:**
- `users` - Benutzer
- `recipes` - Rezepte
- `todos` - Todo-Listen
- `diary_entries` - Tagebuch-Einträge

**Features:**
- Idempotent: Prüft ob Tabellen existieren bevor sie erstellt werden
- Foreign Keys mit `ON DELETE SET NULL`
- Performance-Indizes auf häufig genutzte Spalten
- Default-Werte für Timestamps

---

### 0002 - Add Rating to Diary (2025-11-09)
**File:** `20251109_1400_002_add_rating_to_diary.py`

**Changes:**
- `rating` Spalte zu `diary_entries` hinzugefügt
- Migration existierender Ratings von `recipes` zu `diary_entries`

**Reason:** Rating sollte pro Tagebuch-Eintrag sein, nicht pro Rezept (ein Rezept kann mehrmals gekocht werden mit verschiedenen Bewertungen)

**Idempotent:** Prüft ob Spalte bereits existiert

---

### 0003 - Add Happiness to Diary (2025-11-09)
**File:** `20251109_1500_0003_add_happiness_to_diary.py`

**Changes:**
- `happiness` Spalte zu `diary_entries` hinzugefügt

**Reason:** Feature-Versuch: Glücksfaktor neben Rating

**Status:** Wieder entfernt in 0004

---

### 0004 - Remove Happiness from Diary (2025-11-10)
**File:** `20251110_2100_0004_remove_happiness_from_diary.py`

**Changes:**
- `happiness` Spalte von `diary_entries` entfernt

**Reason:** Feature-Rollback - Glücksfaktor wurde nicht benötigt

---

## ⚙️ Alembic Configuration

### Config Files

**Root-Level Configs:**
- `alembic.ini` - Basis-Konfiguration (für DEV)
- `alembic-prod.ini` - PROD Database Connection
- `alembic-test.ini` - TEST Database Connection

### Environment Detection (env.py)

**Automatische Umgebungs-Erkennung:**
```python
TESTING_MODE=true  → seaser-postgres-test/rezepte_test
DEV_MODE=true      → seaser-postgres-dev/rezepte_dev
(keine ENV)        → seaser-postgres/rezepte (PROD)
```

**Database URLs werden automatisch konstruiert basierend auf ENV Vars:**
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`

---

## 🚀 Migration Commands

### Neue Migration erstellen

```bash
# Im Working Directory
alembic revision -m "add_column_xyz"

# File wird erstellt in: migrations/versions/YYYYMMDD_HHMM_XXXX_add_column_xyz.py
```

**Wichtig:** Revision ID manuell setzen (z.B. `0005`)

---

### Migration anwenden

#### PROD
```bash
# Im PROD Container
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini upgrade head

# Oder während Deployment (automatisch)
./scripts/prod/deploy.sh <tag>
```

#### DEV
```bash
# Im DEV Container
podman exec seaser-rezept-tagebuch-dev alembic upgrade head

# Oder während Build (automatisch)
./scripts/dev/build.sh
```

#### TEST
```bash
# Im TEST Container
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini upgrade head

# Oder während Test-Workflow (automatisch)
./scripts/test/test-and-approve-for-prod.sh
```

---

### Migration Status

```bash
# PROD
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini current

# DEV
podman exec seaser-rezept-tagebuch-dev alembic current

# TEST
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini current

# History
podman exec seaser-rezept-tagebuch alembic history --verbose
```

---

### Migration Downgrade

```bash
# Eine Migration zurück
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini downgrade -1

# Zu spezifischer Revision
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini downgrade 0003

# Alle zurück
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini downgrade base
```

**⚠️ Achtung:** Downgrade kann Datenverlust bedeuten!

---

## 📋 Best Practices

### 1. Idempotente Migrations

Prüfe ob Tabellen/Spalten existieren:

```python
def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Prüfe Tabelle
    existing_tables = inspector.get_table_names()
    if 'my_table' not in existing_tables:
        op.create_table('my_table', ...)

    # Prüfe Spalte
    columns = [col['name'] for col in inspector.get_columns('my_table')]
    if 'my_column' not in columns:
        op.add_column('my_table', sa.Column('my_column', ...))
```

### 2. Daten-Migration

Nutze `op.execute()` für SQL:

```python
def upgrade():
    # Spalte hinzufügen
    op.add_column('diary_entries', sa.Column('rating', sa.Integer()))

    # Daten migrieren
    op.execute("""
        UPDATE diary_entries
        SET rating = recipes.rating
        FROM recipes
        WHERE diary_entries.recipe_id = recipes.id
    """)
```

### 3. Downgrade implementieren

Immer reversible Migrations schreiben:

```python
def downgrade():
    op.drop_column('diary_entries', 'rating')
```

### 4. Foreign Keys

Immer mit `ON DELETE` Policy:

```python
sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL')
```

### 5. Indizes für Performance

Auf häufig genutzte Filter/Joins:

```python
op.create_index('idx_recipes_user_id', 'recipes', ['user_id'])
op.create_index('idx_recipes_auto_imported', 'recipes', ['auto_imported'])
```

---

## 🐛 Troubleshooting

### Migration hängt

```bash
# Prüfe aktive Connections
podman exec seaser-postgres psql -U postgres -d rezepte -c "SELECT * FROM pg_stat_activity WHERE datname='rezepte';"

# Terminate blocking queries
podman exec seaser-postgres psql -U postgres -d rezepte -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='rezepte' AND pid <> pg_backend_pid();"
```

### Alembic Version Conflict

```bash
# Prüfe aktuelle Version
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini current

# Stamp zu spezifischer Version (⚠️ nur wenn DB-State bekannt!)
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini stamp 0004
```

### Migration fehlgeschlagen

```bash
# Logs prüfen
podman logs seaser-rezept-tagebuch | grep alembic

# DB-State prüfen
podman exec seaser-postgres psql -U postgres -d rezepte -c "SELECT * FROM alembic_version;"

# Manuelle Korrektur (als letzter Ausweg)
podman exec -it seaser-postgres psql -U postgres -d rezepte
```

---

## 📚 Weiterführende Links

- **Alembic Docs:** https://alembic.sqlalchemy.org/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/

---

**Erstellt:** 2025-11-11
**Letzte Migration:** 0004 (2025-11-10)
