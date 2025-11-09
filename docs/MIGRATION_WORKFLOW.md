# Migration Workflow mit Alembic

## Übersicht

Der Migration-Workflow stellt sicher, dass Datenbank-Änderungen systematisch getestet werden, bevor sie auf Produktion deployed werden.

**🔒 Sicherheit**: PROD-Deployments sind nur mit freigegebenen Git-Tags möglich, die erfolgreich auf TEST getestet wurden!

## Workflow-Schritte

```
1. DEV: Migration erstellen + Code committen
2. TAG: Git-Tag erstellen
3. TEST: test-migration.sh <TAG> → Tests + Freigabe
4. DEV: Manuelles Testen (optional)
5. PROD: deploy-prod.sh <TAG> → prüft Freigabe → deployed
```

## 🔐 Test-Freigabe-System

**Konzept**: Ein Tag kann nur auf PROD deployed werden, wenn er vorher erfolgreich auf TEST getestet wurde.

**Freigabe-File**: `.test-approvals` (nicht in Git)
```
rezept_version_09_11_2025_002|abc123def|2025-11-09 14:30:15|SUCCESS
```

**Format**: `TAG|COMMIT_HASH|TIMESTAMP|STATUS`

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

## 2. Git-Tag erstellen

```bash
git add migrations/
git commit -m "feat: add new migration"
git tag -a rezept_version_09_11_2025_003 -m "Release: description"
```

---

## 3. Migration auf TEST anwenden + Tests + Freigabe

### Automatischer Test-Workflow mit Freigabe

```bash
./scripts/database/test-migration.sh rezept_version_09_11_2025_003
```

**⚠️ WICHTIG**: Git-Tag als Parameter erforderlich!

**Was passiert**:
1. ✅ Validiert Git-Tag Format
2. ✅ Prüft ob Tag existiert
3. ✅ Baut TEST Container **aus Git-Tag** (nicht Working Dir!)
4. ✅ Startet TEST Container
5. ✅ Führt Alembic Migration auf TEST DB aus
6. ✅ Führt automatische Tests aus (pytest)
7. ✅ **Bei Erfolg: Tag wird für PROD freigegeben** → `.test-approvals`
8. ✅ Optional: DEV Container updaten

**Bei Erfolg**:
- Alle Tests grün ✅
- Tag in `.test-approvals` eingetragen ✅
- Bereit für PROD Deployment ✅

**Bei Fehler**:
- Migration war erfolgreich, aber Tests fehlgeschlagen ❌
- Tag wird **NICHT** freigegeben ❌
- PROD Deployment **blockiert** ❌

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

## 4. DEV umstellen für manuelles Testen (Optional)

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

---

## 5. PROD Deployment mit automatischer Migration

### Deployment starten

```bash
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_003
```

**🔒 Sicherheitscheck**: Script prüft zuerst ob Tag auf TEST freigegeben wurde!

**Was passiert**:
1. ✅ Working Directory Clean Check
2. ✅ Git Tag Validierung
3. ✅ **Prüfung: Tag in `.test-approvals`?** ← **NEU: BLOCKIERT wenn nicht getestet!**
4. ✅ Git Tag Export
5. ✅ Database Backup
6. ✅ Container Image Build
7. ✅ **Alembic Migration auf PROD DB**
8. ✅ PROD Container Neustart
9. ✅ Systemd Service Update

**❌ Deployment wird blockiert wenn**:
- Tag nicht auf TEST getestet wurde
- Keine `.test-approvals` Datei existiert
- Tag nicht in Freigabe-Liste

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

## Beispiel: Kompletter Workflow mit Freigabe-System

```bash
# 1. Migration erstellen in DEV
vim migrations/versions/20251109_1100_003_add_new_field.py

# 2. Code committen
git add migrations/
git commit -m "feat: add new field to recipes"

# 3. Git-Tag erstellen
git tag -a rezept_version_09_11_2025_003 -m "Release: add new field"

# 4. TEST: Migration + Tests + Freigabe
./scripts/database/test-migration.sh rezept_version_09_11_2025_003
# ✅ Container aus Tag gebaut
# ✅ Migration erfolgreich
# ✅ Alle Tests bestanden
# ✅ Tag für PROD freigegeben!

# 5. Optional: DEV Manuelles Testen
# (wird nach test-migration.sh gefragt)
# → Teste in Browser: http://192.168.2.139:8001/rezept-tagebuch/

# 6. PROD Deployment (prüft Freigabe!)
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_003
# ✅ Tag-Freigabe geprüft: 2025-11-09 14:30:15
# ✅ Backup erstellt
# ✅ Migration auf PROD angewendet
# ✅ Container neu gestartet
```

### 🚫 Beispiel: Deployment ohne Test-Freigabe (blockiert!)

```bash
# Neuen Tag erstellen
git tag -a rezept_version_09_11_2025_004 -m "Release: hotfix"

# Direkt auf PROD deployen versuchen (OHNE test-migration.sh)
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_004

# ❌ FEHLER:
# ❌ Tag 'rezept_version_09_11_2025_004' wurde nicht auf TEST freigegeben!
#
# Dieser Tag wurde noch nicht erfolgreich auf TEST getestet.
#
# Test-Workflow starten:
#   ./scripts/database/test-migration.sh rezept_version_09_11_2025_004
```

---

## Zusammenfassung

| Schritt | Script | Umgebung | Migration | Tests | Freigabe |
|---------|--------|----------|-----------|-------|----------|
| 1. Erstellen | - | DEV | Manuell | - | - |
| 2. Tag | `git tag` | - | - | - | - |
| 3. TEST | `test-migration.sh <TAG>` | TEST | ✅ Auto | ✅ Auto | ✅ Bei Erfolg |
| 4. DEV Update | `build-dev.sh` | DEV | ✅ Auto | Manuell | - |
| 5. PROD | `deploy-prod.sh <TAG>` | PROD | ✅ Auto | - | 🔒 Prüft! |

**🔒 Sicherheit**:
- Jede Migration wird auf TEST getestet bevor PROD
- PROD-Deployment **blockiert** ohne Test-Freigabe
- Nur Git-Tags können deployed werden
- Tags werden aus exaktem Git-Snapshot gebaut
