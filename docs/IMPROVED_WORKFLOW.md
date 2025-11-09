# Verbesserter DEV → TEST → PROD Workflow mit Alembic

## 🎯 Ziel

Systematischer Workflow der sicherstellt, dass:
1. ✅ Migrations auf DEV zuerst getestet werden (manuell)
2. ✅ Automated Tests auf TEST laufen (inkl. Feature-Tests)
3. ✅ Nur getesteter Code auf PROD kommt
4. ✅ Alembic Migrations linear bleiben (0001 → 0002 → 0003)

## 📋 Workflow-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: DEV Development & Manual Testing                   │
├─────────────────────────────────────────────────────────────┤
│ 1. Migration erstellen (z.B. 0003_add_rating.py)           │
│ 2. Code ändern (app.py, index.html)                        │
│ 3. build-dev.sh → alembic upgrade head auf DEV DB          │
│ 4. Manuell testen in Browser (http://...8001/...)          │
│ 5. git commit (NOCH KEIN TAG!)                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: TEST Automated Testing                             │
├─────────────────────────────────────────────────────────────┤
│ 6. test-migration.sh (OHNE Parameter, nutzt HEAD)          │
│    → Baut Container aus Working Dir (git archive HEAD)     │
│    → alembic upgrade head auf TEST DB                      │
│    → pytest: CRUD + Migration + Feature Tests              │
│    → Schreibt .test-approvals mit COMMIT_HASH               │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Tagging & Production                               │
├─────────────────────────────────────────────────────────────┤
│ 7. git tag rezept_version_DD_MM_YYYY_NNN                   │
│ 8. deploy-prod.sh <tag>                                     │
│    → Prüft ob COMMIT_HASH von Tag in .test-approvals       │
│    → alembic upgrade head auf PROD DB                      │
│    → Deploy                                                 │
└─────────────────────────────────────────────────────────────┘
```

## 🗄️ Datenbank-Status während Workflow

```
SCHRITT          DEV DB        TEST DB       PROD DB
─────────────────────────────────────────────────────
Initial          0002          0002          0002
Dev Testing      0003          0002          0002
Test Phase       0003          0003          0002
Production       0003          0003          0003
```

## 📝 Detaillierte Schritte

### Phase 1️⃣: DEV Development

#### Schritt 1: Migration erstellen

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Neue Migration erstellen
vim migrations/versions/20251109_1500_003_add_feature.py
```

**Migration Template:**
```python
"""Add new feature

Revision ID: 0003
Revises: 0002
Create Date: 2025-11-09 15:00:00.000000

Changes:
- Detaillierte Beschreibung der Änderungen
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Apply changes"""
    op.execute("""
        -- SQL hier
    """)

def downgrade() -> None:
    """Revert changes"""
    op.execute("""
        -- SQL hier
    """)
```

#### Schritt 2: Code ändern

```bash
# Frontend ändern
vim index.html

# Backend ändern
vim app.py

# Models ändern
vim models.py
```

#### Schritt 3: DEV Container aktualisieren

```bash
./scripts/deployment/build-dev.sh
```

**Was passiert:**
- ✅ Container baut mit neuer Migration
- ✅ Container startet
- ✅ `alembic upgrade head` läuft automatisch
- ✅ DEV DB: 0002 → 0003

#### Schritt 4: Manuell testen

```bash
# Browser öffnen
xdg-open http://192.168.2.139:8001/rezept-tagebuch/

# Feature testen:
# - UI Elemente vorhanden?
# - Daten korrekt migriert?
# - Keine Fehler in Console?
# - Alle User-Flows funktionieren?

# DEV DB inspizieren
podman exec seaser-postgres-dev psql -U postgres -d rezepte_dev -c "\d+ tablename"
```

#### Schritt 5: Code committen

```bash
git add migrations/ app.py index.html models.py
git commit -m "feat: add new feature with migration 0003"

# WICHTIG: NOCH KEIN TAG!
```

### Phase 2️⃣: TEST Automated Testing

#### Schritt 6: Automated Tests

```bash
./scripts/database/test-migration.sh
```

**Was passiert:**
1. ✅ Baut Container aus **Working Directory** (HEAD)
2. ✅ Startet TEST Container
3. ✅ `alembic upgrade head` auf TEST DB: 0002 → 0003
4. ✅ Führt pytest aus:
   - CRUD Tests (test_recipes_crud.py, test_diary_crud.py)
   - Migration Tests (test_migrations.py)
   - **Feature Tests (test_rating_feature.py)** ← NEU!
5. ✅ Bei Erfolg: Schreibt `.test-approvals` mit COMMIT_HASH

**Beispiel .test-approvals:**
```
abc123def456|2025-11-09 15:30:00|SUCCESS
```

**Format:** `COMMIT_HASH|TIMESTAMP|STATUS`

#### Feature Tests schreiben

Für jede neue Feature sollte ein Test erstellt werden:

```bash
vim tests/test_rating_feature.py
```

**Beispiel:**
```python
def test_rating_migration_from_recipes_to_diary(api_client):
    """Test dass Ratings von recipes zu diary_entries migriert wurden"""
    # 1. Recipe mit Rating erstellen
    recipe = api_client.post('/api/recipes', json={
        'title': 'Test Recipe',
        'rating': 5
    })

    # 2. Diary Entry erstellen
    entry = api_client.post('/api/diary', json={
        'recipe_id': recipe['id'],
        'date': '2025-11-09',
        'dish_name': 'Test'
    })

    # 3. Prüfen: Entry hat Rating vom Recipe übernommen
    assert entry['rating'] == 5
```

### Phase 3️⃣: Tagging & Production

#### Schritt 7: Git Tag erstellen

```bash
# Nur wenn Phase 2 erfolgreich war!
git tag -a rezept_version_09_11_2025_005 -m "Release: neue Feature mit Rating Migration"
```

#### Schritt 8: PROD Deployment

```bash
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_005
```

**Was passiert:**
1. ✅ Prüft: Ist COMMIT_HASH vom Tag in `.test-approvals`?
2. ✅ Backup PROD DB
3. ✅ Baut Container aus Git-Tag
4. ✅ `alembic upgrade head` auf PROD DB: 0002 → 0003
5. ✅ Startet PROD Container
6. ✅ Systemd Service Update

**Sicherheitscheck:**
```bash
# Tag COMMIT_HASH
git rev-parse rezept_version_09_11_2025_005
# → abc123def456

# In .test-approvals?
grep "abc123def456" .test-approvals
# → abc123def456|2025-11-09 15:30:00|SUCCESS
# ✅ Match! Deployment erlaubt
```

## 🔒 Sicherheits-Features

### 1. Test-Freigabe-System

- ❌ PROD Deployment **blockiert** ohne Test-Freigabe
- ✅ Freigabe basiert auf **COMMIT_HASH**, nicht Tag-Name
- ✅ Tag kann umbenannt/verschoben werden, Hash bleibt gleich

### 2. Linear Migrations

- ✅ Alembic erzwingt Reihenfolge: 0001 → 0002 → 0003
- ❌ Kein "Überspringen" möglich
- ✅ Jede Umgebung holt schrittweise auf

### 3. Rollback-Unterstützung

```bash
# Migration rückgängig machen
podman exec seaser-rezept-tagebuch alembic -c alembic-prod.ini downgrade -1

# Komplettes Rollback
./scripts/deployment/rollback.sh rezept_version_09_11_2025_004
```

## 📊 Vergleich Alt vs. Neu

| Aspekt | ALT (Tag-basiert) | NEU (Commit-basiert) |
|--------|-------------------|----------------------|
| DEV Testing | ❌ Übersprungen | ✅ Manuell, vor TEST |
| TEST Trigger | Git-Tag erforderlich | Working Dir (HEAD) |
| Tag-Zeitpunkt | Vor Tests | Nach erfolgreichen Tests |
| Freigabe | Tag-Name | Commit-Hash |
| Feature Tests | ❌ Fehlen | ✅ Erforderlich |
| Reihenfolge | Tag → TEST → PROD | DEV → TEST → Tag → PROD |

## 🧪 Beispiel: Kompletter Workflow

```bash
# ── Phase 1: DEV Development ──────────────────────────────
cd /home/gabor/easer_projekte/rezept-tagebuch

# Migration erstellen
vim migrations/versions/20251109_1500_003_add_rating_to_diary.py
# revision = '0003', down_revision = '0002'

# Code ändern
vim app.py models.py index.html

# DEV Container aktualisieren
./scripts/deployment/build-dev.sh
# → DEV DB: 0002 → 0003

# Manuell testen
xdg-open http://192.168.2.139:8001/rezept-tagebuch/
# ✅ Rating im Tagebuch-Dialog sichtbar
# ✅ Rating wird gespeichert
# ✅ Migration hat alte Daten übernommen

# Committen
git add migrations/ app.py models.py index.html
git commit -m "feat: move rating from recipes to diary entries"
# Commit: abc123def456

# ── Phase 2: TEST Automated Testing ──────────────────────
# Feature Tests schreiben
vim tests/test_rating_feature.py

git add tests/
git commit -m "test: add rating migration feature tests"
# Commit: def789ghi012

# TEST laufen lassen
./scripts/database/test-migration.sh
# ✅ Container aus HEAD gebaut
# ✅ TEST DB: 0002 → 0003
# ✅ pytest: 32 passed
# ✅ .test-approvals: def789ghi012|2025-11-09 15:30:00|SUCCESS

# ── Phase 3: Tagging & Production ────────────────────────
# Tag erstellen
git tag -a rezept_version_09_11_2025_005 -m "Release: rating migration"

# PROD Deployment
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_005
# ✅ Prüft: git rev-parse rezept_version_09_11_2025_005 → def789ghi012
# ✅ Prüft: grep def789ghi012 .test-approvals → FOUND
# ✅ Backup PROD DB
# ✅ PROD DB: 0002 → 0003
# ✅ Deploy erfolgreich
```

## 🚨 Fehlerbehandlung

### Tests schlagen fehl auf TEST

```bash
./scripts/database/test-migration.sh
# ❌ FAILED tests/test_rating_feature.py::test_rating_display

# Debugging:
# 1. TEST Container Logs
podman logs seaser-rezept-tagebuch-test --tail 50

# 2. TEST DB inspizieren
podman exec seaser-postgres-test psql -U postgres -d rezepte_test

# 3. TEST Container interaktiv
podman exec -it seaser-rezept-tagebuch-test bash
pytest -v -s -k test_rating_display

# Fehler beheben:
vim app.py
git add app.py
git commit -m "fix: rating display logic"

# Erneut testen:
./scripts/database/test-migration.sh
```

### PROD Deployment blockiert

```bash
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_005
# ❌ FEHLER: Commit def789ghi012 nicht in .test-approvals!

# Lösung: Tests zuerst laufen lassen
./scripts/database/test-migration.sh
# Dann erneut deployen
./scripts/deployment/deploy-prod.sh rezept_version_09_11_2025_005
```

### Migration fehlgeschlagen

```bash
# DEV/TEST: Downgrade und neu testen
podman exec seaser-rezept-tagebuch-test alembic -c alembic-test.ini downgrade -1

# PROD: Rollback auf vorherigen Tag
./scripts/deployment/rollback.sh rezept_version_09_11_2025_004
```

## ✅ Best Practices

1. **DEV zuerst testen** - Immer manuell in DEV testen vor TEST
2. **Feature Tests schreiben** - Jede neue Feature braucht Tests
3. **Kleine Migrations** - Lieber mehrere kleine statt eine große
4. **Downgrade implementieren** - Immer Rollback-Fähigkeit sicherstellen
5. **Commit Messages** - Klare Beschreibung was geändert wurde
6. **Migration Beschreibung** - Docstring mit Details was migriert wird

## 📚 Siehe auch

- [MIGRATION_WORKFLOW.md](./MIGRATION_WORKFLOW.md) - Alembic Details
- [GIT-TAG-WORKFLOW.md](./GIT-TAG-WORKFLOW.md) - Git Tagging Convention
- [tests/README.md](../tests/README.md) - Test Suite Dokumentation
