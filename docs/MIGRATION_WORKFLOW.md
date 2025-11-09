# Migration Workflow mit Alembic

## Übersicht

Der Migration-Workflow stellt sicher, dass Datenbank-Änderungen systematisch getestet werden, bevor sie auf Produktion deployed werden.

## Workflow-Schritte

```
1. DEV: Migration erstellen
2. TEST: Migration + automatische Tests
3. DEV: Umstellen auf neue Version (manuelles Testen)
4. TAG: Erstellen bei Freigabe
5. PROD: Automatische Migration + Deployment
```

---

## 1. Migration in DEV erstellen

### Neue Migration erstellen

```bash
# In DEV-Umgebung
cd /home/gabor/easer_projekte/rezept-tagebuch

# Manuelle Migration erstellen (empfohlen)
touch migrations/versions/YYYYMMDD_HHMM_NNNN_beschreibung.py
```

**Format**: `YYYYMMDD_HHMM_NNNN_beschreibung.py`
- `YYYYMMDD`: Datum
- `HHMM`: Uhrzeit
- `NNNN`: Revisions-Nummer (0001, 0002, etc.)
- `beschreibung`: Kurze Beschreibung

**Beispiel**: `20251109_1100_002_rename_imported_at_to_erstellt_am.py`

### Migration-Template

```python
"""Kurze Beschreibung

Revision ID: 0002
Revises: 0001
Create Date: 2025-11-09 11:00:00.000000

Changes:
- Liste der Änderungen
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade database schema"""
    # Deine SQL-Befehle hier
    op.execute("""
        -- SQL hier
    """)

def downgrade() -> None:
    """Revert database schema"""
    # Rollback SQL hier
    op.execute("""
        -- SQL hier
    """)
```

---

## 2. Migration auf TEST anwenden + Tests

### Automatischer Test-Workflow

```bash
./scripts/database/test-migration.sh
```

**Was passiert**:
1. ✅ TEST Container wird gebaut
2. ✅ TEST Container wird gestartet
3. ✅ Alembic Migration wird auf TEST DB angewendet
4. ✅ Automatische Tests laufen (pytest)
5. ✅ Optional: DEV Container updaten

**Bei Erfolg**: Alle Tests grün ✅
**Bei Fehler**: Migration war erfolgreich, aber Tests fehlgeschlagen ❌

### Manuelle Prüfung auf TEST

```bash
# TEST Container Logs
podman logs seaser-rezept-tagebuch-test

# TEST DB Schema prüfen
podman exec seaser-postgres-test psql -U postgres -d rezepte_test -c "\d+ recipes"

# TEST API aufrufen
curl http://192.168.2.139:8000/rezept-tagebuch-test/api/recipes
```

---

## 3. DEV umstellen für manuelles Testen

### DEV Container aktualisieren

```bash
./scripts/deployment/build-dev.sh
```

**Was passiert**:
1. ✅ DEV Container wird mit neuer Migration gebaut
2. ✅ DEV Container wird neu gestartet
3. ✅ Migration wird automatisch angewendet

### Manuelles Testen in DEV

1. Öffne: http://192.168.2.139:8001/rezept-tagebuch/
2. Teste alle betroffenen Features
3. Prüfe ob Daten korrekt migriert wurden
4. Teste Edge-Cases

**Freigabe**: Wenn alles funktioniert → Git Tag erstellen

---

## 4. Git Tag erstellen bei Freigabe

### Tag automatisch erstellen

```bash
./scripts/tools/tag-version.sh
```

**Format**: `rezept_version_DD_MM_YYYY_NNN`
**Beispiel**: `rezept_version_09_11_2025_001`

### Tag manuell erstellen

```bash
git tag -a rezept_version_09_11_2025_001 -m "Release: erstellt_am field for all recipes"
git push origin rezept_version_09_11_2025_001
```

---

## 5. PROD Deployment mit automatischer Migration

### Deployment starten

```bash
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_001
```

**Was passiert**:
1. ✅ Working Directory Clean Check
2. ✅ Git Tag Validierung
3. ✅ Git Tag Export
4. ✅ Database Backup
5. ✅ Container Image Build
6. ✅ **Alembic Migration auf PROD DB** ← NEU
7. ✅ PROD Container Neustart
8. ✅ Systemd Service Update

**Migration auf PROD**:
- Läuft in temporärem Container
- Verwendet `alembic-prod.ini`
- `alembic upgrade head`
- Automatisch vor Container-Start

---

## Alembic Konfiguration

### Config-Dateien

| Datei | Umgebung | DB Connection |
|-------|----------|---------------|
| `alembic.ini` | Base Config | `seaser-postgres/rezepte` |
| `alembic-test.ini` | TEST | `seaser-postgres-test/rezepte_test` |
| `alembic-prod.ini` | PROD | `seaser-postgres/rezepte` |

### Manuelle Alembic-Befehle

```bash
# Im Container ausführen
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini current
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini history
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini upgrade head
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini downgrade -1
```

---

## Automatische Tests

### Test-Datei: `tests/test_migrations.py`

**Was wird getestet**:
- ✅ Alembic Version Tabelle existiert
- ✅ Migration Version ist gesetzt
- ✅ Schema ist korrekt (alle Spalten vorhanden)
- ✅ Foreign Keys existieren
- ✅ Default-Werte sind gesetzt
- ✅ Alte Spalten sind entfernt

### Tests manuell ausführen

```bash
# Im TEST Container
podman exec seaser-rezept-tagebuch-test pytest tests/test_migrations.py -v

# Lokal (gegen TEST DB)
POSTGRES_HOST=seaser-postgres-test POSTGRES_DB=rezepte_test pytest tests/test_migrations.py -v
```

---

## Troubleshooting

### Migration fehlgeschlagen auf TEST

```bash
# Logs prüfen
podman logs seaser-rezept-tagebuch-test

# Shell im Container
podman exec -it seaser-rezept-tagebuch-test bash

# Alembic Status
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini current

# Manuelle Downgrade
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini downgrade -1
```

### Tests fehlgeschlagen

```bash
# Detaillierte Test-Ausgabe
podman exec seaser-rezept-tagebuch-test pytest tests/test_migrations.py -v -s

# Nur einen Test
podman exec seaser-rezept-tagebuch-test pytest tests/test_migrations.py::test_recipes_table_schema -v
```

### PROD Migration fehlgeschlagen

**⚠️ WICHTIG**: Deployment stoppt bei Migration-Fehler!

```bash
# Backup restore (falls nötig)
./scripts/database/restore-db.sh data/prod/backups/rezepte-backup-before-rezept_version_09_11_2025_001.sql

# Rollback
./scripts/deployment/rollback.sh rezept_version_08_11_2025_003
```

---

## Best Practices

### DO ✅

- **Immer erst auf TEST testen** bevor DEV/PROD
- **Tests schreiben** für Schema-Änderungen
- **Downgrade implementieren** für Rollback
- **Backup vor PROD** wird automatisch erstellt
- **Git Tag nur bei erfolgreichen Tests** erstellen

### DON'T ❌

- **NICHT direkt auf PROD migrieren** ohne TEST
- **NICHT Migrations überspringen** (Reihenfolge wichtig!)
- **NICHT Migration ohne Downgrade** (Rollback unmöglich)
- **NICHT Schema manuell ändern** (nur via Alembic)

---

## Beispiel: Kompletter Workflow

```bash
# 1. Migration erstellen in DEV
vim migrations/versions/20251109_1100_002_rename_imported_at_to_erstellt_am.py

# 2. TEST: Migration + Tests
./scripts/database/test-migration.sh
# ✅ Migration erfolgreich
# ✅ Alle Tests bestanden

# 3. DEV: Manuelles Testen
# (wird automatisch nach test-migration.sh gefragt)
# → Teste in Browser: http://192.168.2.139:8001/rezept-tagebuch/

# 4. Tag erstellen
git add migrations/
git commit -m "feat: rename imported_at to erstellt_am for all recipes"
./scripts/tools/tag-version.sh

# 5. PROD Deployment
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_001
# ✅ Backup erstellt
# ✅ Migration auf PROD angewendet
# ✅ Container neu gestartet
```

---

## Zusammenfassung

| Schritt | Script | Umgebung | Migration | Tests |
|---------|--------|----------|-----------|-------|
| 1. Erstellen | - | DEV | Manuell | - |
| 2. TEST | `test-migration.sh` | TEST | ✅ Auto | ✅ Auto |
| 3. DEV Update | `build-dev.sh` | DEV | ✅ Auto | Manuell |
| 4. Tag | `tag-version.sh` | - | - | - |
| 5. PROD | `deploy-prod.sh` | PROD | ✅ Auto | - |

**Sicherheit**: Jede Migration wird zweimal getestet (TEST + DEV) bevor sie auf PROD kommt!
