# Verbesserter DEV → TEST → PROD Workflow mit Alembic

**Version:** v25.11.10
**Update:** Vereinfachte Container-Config (nur TESTING_MODE / DEV_MODE, keine redundanten ENV vars)

## 🎯 Ziel

Systematischer Workflow der sicherstellt, dass:
1. ✅ Migrations auf DEV zuerst getestet werden (manuell)
2. ✅ Automated Tests auf TEST laufen (inkl. Feature-Tests)
3. ✅ Nur getesteter Code auf PROD kommt
4. ✅ Alembic Migrations linear bleiben (0001 → 0002 → 0003)
5. ✅ Container-Konfiguration ist vereinfacht und konsistent

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

## 🐳 Container-Konfiguration (v25.11.10)

Seit v25.11.10 verwenden alle Umgebungen **vereinfachte Container-Configs**:

### Automatische Umgebungserkennung

Die `config.py` erkennt automatisch die Umgebung und wählt die richtige Datenbank:

```python
# DEV: -e DEV_MODE=true
if DEV_MODE:
    db = postgresql://postgres:seaser@seaser-postgres-dev:5432/rezepte_dev
    uploads = /data/dev/uploads

# TEST: -e TESTING_MODE=true
if TESTING_MODE:
    db = postgresql://postgres:test@seaser-postgres-test:5432/rezepte_test
    uploads = /data/test/uploads

# PROD: (keine Environment Variable)
else:
    db = postgresql://postgres:seaser@seaser-postgres:5432/rezepte
    uploads = /data/uploads
```

**Keine redundanten Environment Variables mehr nötig!**
- ❌ Früher: `-e DB_TYPE -e POSTGRES_HOST -e POSTGRES_DB -e POSTGRES_USER -e POSTGRES_PASSWORD`
- ✅ Jetzt: Nur `-e DEV_MODE=true` oder `-e TESTING_MODE=true`

**Details:** Siehe `docs/DATABASE-STORAGE.md` für vollständige Architektur.

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
2. ✅ Startet TEST Container (on-demand, nur `-e TESTING_MODE=true`)
3. ✅ `alembic upgrade head` auf TEST DB: 0002 → 0003
4. ✅ Führt pytest aus:
   - CRUD Tests (test_recipes_crud.py, test_diary_crud.py)
   - Migration Tests (test_migrations.py)
   - **Feature Tests (test_rating_feature.py)** ← NEU!
5. ✅ Bei Erfolg: Schreibt `.test-approvals` mit COMMIT_HASH
6. ✅ Stoppt TEST Container automatisch (on-demand only)

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

## 🐛 Lessons Learned aus Workflow-Test (09.11.2025)

Beim ersten kompletten Durchlauf des Workflows wurden folgende Issues gefunden und behoben:

### Issue 1: API URL Doubling (26 Tests failing)
**Symptom:** Tests riefen `/api/api/recipes` statt `/api/recipes` auf → 405 Method Not Allowed

**Root Cause:**
- `API_BASE_URL = "http://localhost:80"` (ohne /api)
- Tests verwendeten `'/api/recipes'`
- Konkatenation: `base_url + endpoint` = `http://localhost:80` + `/api/recipes` ✓

**Fix:**
- `API_BASE_URL = "http://localhost:80/api"` (mit /api)
- Tests verwenden `'/recipes'` (ohne /api)
- Konkatenation: `base_url + endpoint` = `http://localhost:80/api` + `/recipes` = `/api/recipes` ✓

**Dateien:** `tests/conftest.py`, `tests/test_rating_feature.py`

### Issue 2: Cleanup Fixture API Change (7 Tests failing)
**Symptom:** `TypeError: 'list' object is not callable`

**Root Cause:**
- Fixture `cleanup_test_diary_entries` änderte von Funktion zu List
- Tests verwendeten noch `cleanup_test_diary_entries(id)`

**Fix:** Alle Calls geändert zu `cleanup_test_diary_entries.append(id)`

**Dateien:** `tests/test_diary_crud.py` (7 Stellen)

### Issue 3: Partial Update Bug (1 Test failing)
**Symptom:** `PUT /api/diary/{id}` mit nur `{'rating': 4}` → 500 Error

**Root Cause:**
```python
# ALT (BROKEN):
entry.date = datetime.fromisoformat(data.get('date')).date() if data.get('date') else None
# Setzt date=None wenn nur rating geschickt wird → NOT NULL Constraint violated
```

**Fix:** Nur Felder updaten die im Request vorhanden sind:
```python
# NEU (FIXED):
if 'date' in data:
    entry.date = datetime.fromisoformat(data['date']).date()
if 'rating' in data:
    entry.rating = data['rating']
```

**Dateien:** `app.py` (update_diary_entry function, Zeilen 589-635)

### Issue 4: Migration Test zu strikt (1 Test failing)
**Symptom:** Test erwartet database-level DEFAULT für `erstellt_am`

**Root Cause:** TEST DB aus altem Schema erstellt, SQLAlchemy handled DEFAULT auf Python-Level

**Fix:** Test relaxiert um NULL defaults zu erlauben

**Dateien:** `tests/test_migrations.py:216-235`

### Issue 5: Tests nicht im Container (0 Tests found)
**Symptom:** `pytest` findet keine Tests → `collected 0 items`

**Root Cause:** Containerfile kopierte `tests/` Directory nicht ins Image

**Fix:**
```dockerfile
COPY tests/ tests/
COPY pytest.ini .
```

**Dateien:** `Containerfile`

### Issue 6: deploy-prod.sh Annotated Tag Bug
**Symptom:** Deployment blockiert mit "Commit '53b32e1' nicht freigegeben", obwohl commit 565165e freigegeben ist

**Root Cause:**
```bash
# ALT (BROKEN):
TAG_COMMIT_HASH=$(git rev-parse "$GIT_TAG")
# Gibt bei annotated tags den Tag-Object Hash zurück (53b32e1), nicht den Commit Hash
```

**Fix:**
```bash
# NEU (FIXED):
TAG_COMMIT_HASH=$(git rev-parse "$GIT_TAG^{commit}")
# ^{commit} dereferenziert annotated tags zum eigentlichen Commit (565165e)
```

**Dateien:** `scripts/deployment/deploy-prod.sh:83-84`

**Commit:** `95f768f` - Fix deploy-prod.sh to handle annotated git tags correctly

---

## 📋 Git Tag Konventionen

### Tag-Format

**Pattern:** `rezept_version_DD_MM_YYYY_NNN`

**Beispiele:**
- `rezept_version_09_11_2025_001` → zeigt als `v09.11.25-1`
- `rezept_version_09_11_2025_002` → zeigt als `v09.11.25-2`

**Ungültige Formate:**
- ❌ `v1.0.0`
- ❌ `rezept_version_9_11_2025_001` (Tag/Monat muss 2-stellig sein)
- ❌ `rezept_version_09_11_2025_1` (Build muss 3-stellig sein: 001)

### Tag erstellen

**Manuell (nach erfolgreichen Tests):**
```bash
git tag -a rezept_version_09_11_2025_005 -m "Release: happiness feature migration 0003"
```

**Mit Helper-Script (nicht empfohlen für diesen Workflow):**
```bash
./scripts/tools/tag-version.sh
# Führt alte Test-Suite aus, NICHT den neuen test-migration.sh Workflow
```

**Wichtig:** Tags IMMER **nach** erfolgreichen Tests erstellen, nicht vorher!

---

## 📚 Siehe auch

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment Scripts Details
- [MIGRATIONS.md](./MIGRATIONS.md) - Alembic Migration Details
- [tests/README.md](../tests/README.md) - Test Suite Dokumentation
