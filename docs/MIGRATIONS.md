# Database Migrations - Rezept-Tagebuch

**Migration-System:** Alembic
**Version:** 1.13.1

---

## 🎯 Übersicht

Das Rezept-Tagebuch nutzt **Alembic** für versionierte Datenbank-Migrationen. Das bedeutet:

✅ **Schema-Änderungen sind versioniert** (wie Git für Code)
✅ **Rollback möglich** bei jedem Update
✅ **Backup funktioniert immer** - Schema-Version wird gespeichert
✅ **Automatische Migrations** bei Prod-Deployment

---

## 📚 Migration-Befehle

### Prod-Datenbank migrieren

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Aktuelle Version anzeigen
./scripts/database/migrate.sh current prod

# Alle Migrations anwenden
./scripts/database/migrate.sh upgrade prod

# Letzte Migration rückgängig machen
./scripts/database/migrate.sh downgrade prod

# Migration-Historie ansehen
./scripts/database/migrate.sh history prod
```

### Dev-Datenbank migrieren

```bash
# Alle Migrations anwenden
./scripts/database/migrate.sh upgrade dev

# Aktuelle Version anzeigen
./scripts/database/migrate.sh current dev
```

---

## 🔄 Workflow: Neue Schema-Änderung

### Beispiel: Kategorie-Feld hinzufügen

#### 1. Migration erstellen

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch
./scripts/database/migrate.sh create add_kategorie_field
```

Erstellt: `migrations/versions/YYYYMMDD_HHMM_002_add_kategorie_field.py`

#### 2. Migration bearbeiten

```python
# migrations/versions/20251105_1200_002_add_kategorie_field.py

def upgrade() -> None:
    """Add kategorie column to recipes"""
    with op.batch_alter_table('recipes') as batch_op:
        batch_op.add_column(
            sa.Column('kategorie', sa.Text(), nullable=True)
        )

def downgrade() -> None:
    """Remove kategorie column"""
    with op.batch_alter_table('recipes') as batch_op:
        batch_op.drop_column('kategorie')
```

**Wichtig:** Immer `batch_alter_table` für SQLite verwenden!

#### 3. In Dev testen

```bash
# Migration anwenden
./scripts/database/migrate.sh upgrade dev

# App testen: http://192.168.2.139:8000/rezept-tagebuch-dev/

# Bei Problemen: Rollback
./scripts/database/migrate.sh downgrade dev
```

#### 4. Nach Prod deployen

```bash
./scripts/deployment/deploy-prod.sh 25.11.05
```

**Das Script macht automatisch:**
1. ✅ Backup der Prod-DB
2. ✅ Image bauen
3. ✅ **Migrations anwenden**
4. ✅ Container starten

---

## 💾 Backup & Restore mit Migrations

### Backup erstellen

```bash
# Automatisches Backup (inkl. Migration-Version)
./scripts/database/backup-db.sh prod

# Manuelles Backup mit Beschreibung
./scripts/database/backup-db.sh prod "before kategorie feature"
```

**Backup-Format:**
```
rezepte-20251104-210530-001-before-v25.11.05.db
         └─────┬────┘ └┬┘ └──────┬───────────┘
          Timestamp    │    Description
                Migration-Version (wichtig!)
```

### Restore mit Schema-Check

```bash
# Verfügbare Backups anzeigen
./scripts/database/restore-db.sh prod

# Restore (mit Migration-Check)
./scripts/database/restore-db.sh prod rezepte-20251104-210530-001-auto.db
```

**Das Script warnt automatisch:**
- ⚠️ Migration-Version unterschiedlich
- ⚠️ Schema-Kompatibilität prüfen

---

## 🗂️ Migration-Historie

### v2.1 - Initial Schema (Migration 001)

**Datum:** 04.11.2025
**Migration:** `20251104_2100_001_initial_schema.py`

**Tabellen:**
- `users` (id, name, email, avatar_color, created_at)
- `recipes` (id, title, image, notes, duration, rating, user_id, is_system, created_at, updated_at)
- `todos` (id, text, priority, completed, user_id, created_at, updated_at)

**Default-Daten:**
- User "Natalie" (id=1, natalie@seaser.local)

---

## 🔍 Troubleshooting

### Problem: "alembic: command not found"

```bash
# Alembic installieren
pip3 install alembic==1.13.1

# Oder im Container
podman exec seaser-rezept-tagebuch pip install alembic==1.13.1
```

### Problem: Migration-Version stimmt nicht

```bash
# 1. Aktuelle Version prüfen
./scripts/database/migrate.sh current prod

# 2. Backup mit passender Version finden
./scripts/database/restore-db.sh prod

# 3. Restore + Migrations neu anwenden
./scripts/database/restore-db.sh prod rezepte-TIMESTAMP-001-*.db
./scripts/database/migrate.sh upgrade prod
```

### Problem: SQLite "table already exists"

**Ursache:** Datenbank existiert, aber Alembic weiß es nicht

**Lösung:** Alembic auf richtige Version setzen (ohne Migration anzuwenden)

```bash
# Manuell Version markieren (ohne CREATE TABLE auszuführen)
export DB_PATH="/home/gabor/data/rezept-tagebuch/rezepte.db"
alembic stamp 001
```

### Problem: Batch-Alter-Table Fehler

**Ursache:** SQLite unterstützt ALTER TABLE nur begrenzt

**Lösung:** Immer `batch_alter_table` in Migrations verwenden:

```python
# ✅ Richtig (SQLite-kompatibel):
with op.batch_alter_table('recipes') as batch_op:
    batch_op.add_column(...)

# ❌ Falsch (funktioniert nicht in SQLite):
op.add_column('recipes', ...)
```

---

## 📖 Best Practices

### 1. Immer Up & Down definieren

```python
def upgrade() -> None:
    # Schema-Änderung vorwärts
    pass

def downgrade() -> None:
    # Schema-Änderung rückwärts (WICHTIG!)
    pass
```

### 2. Daten-Migrationen separat

```python
def upgrade() -> None:
    # 1. Schema ändern
    with op.batch_alter_table('recipes') as batch_op:
        batch_op.add_column(sa.Column('status', sa.Text()))

    # 2. Default-Werte setzen
    op.execute("UPDATE recipes SET status = 'active' WHERE status IS NULL")
```

### 3. Testen in Dev zuerst

```bash
# IMMER zuerst in Dev testen!
./scripts/database/migrate.sh upgrade dev
# App testen
# Rollback testen: ./scripts/database/migrate.sh downgrade dev
# Dann erst Prod: ./scripts/deployment/deploy-prod.sh
```

### 4. Backup vor großen Änderungen

```bash
# Manuelles Backup vor Schema-Änderung
./scripts/database/backup-db.sh prod "before major schema change"
./scripts/deployment/deploy-prod.sh 25.11.05
```

---

## 🚀 Deployment-Flow mit Migrations

```
┌─────────────────────────────────────────┐
│  1. Code-Änderung + neue Migration      │
│     ./scripts/database/migrate.sh create add_feature     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. Dev testen                          │
│     ./scripts/database/migrate.sh upgrade dev            │
│     Test App, Test Rollback             │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  3. Prod deployen                       │
│     ./scripts/deployment/deploy-prod.sh 25.11.05           │
│     ├─ Auto-Backup (mit Migration-Ver) │
│     ├─ Image bauen                      │
│     ├─ Migrations anwenden              │
│     └─ Container starten                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  4. Bei Problemen: Rollback             │
│     ./scripts/deployment/rollback.sh v25.11.04             │
│     ./scripts/database/restore-db.sh prod (if needed)    │
└─────────────────────────────────────────┘
```

---

## 📝 Weitere Ressourcen

- [Alembic Dokumentation](https://alembic.sqlalchemy.org/)
- [SQLite Batch Operations](https://alembic.sqlalchemy.org/en/latest/batch.html)
- `./scripts/database/migrate.sh help` - Alle verfügbaren Befehle

---

**Erstellt:** 04.11.2025
**Version:** 1.0
