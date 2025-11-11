# Configuration Files

Configuration files für Rezept-Tagebuch, organisiert nach Umgebungen.

---

## 🎯 Struktur

```
config/
├── prod/        PROD-spezifische Configs
├── dev/         DEV-spezifische Configs
├── test/        TEST-spezifische Configs
└── shared/      Umgebungsunabhängige Configs
```

---

## 📁 Shared Configs (config/shared/)

### themealdb-config.json
TheMealDB Import-Konfiguration:
- API Strategien (random, by_category, by_area, etc.)
- Verfügbare Kategorien und Regionen
- Rotation Schedule
- Preferences

**Verwendet von:**
- `app.py` (Daily Import)
- `scripts/prod/automation/daily-import-themealdb.sh`

### migusto-import-config.json
Migusto Import-Konfiguration:
- Base URL und Pfade
- Filter-Definitionen
- Presets (vegetarisch, vegan, Familie, etc.)
- Import-Limits und Delays

**Verwendet von:**
- `app.py` (Migusto Import)
- `import_workers.py`
- `scripts/prod/automation/daily-import-migusto.sh`

### recipe-format-config.json
Rezept-Parser-Konfiguration:
- Regex-Patterns für Schritte, Zutaten, Metadaten
- Section-Order und Display-Styles
- Fallback-Verhalten

**Verwendet von:**
- `index.html` (Frontend parseRecipeNotes())
- API: `/api/recipe-format-config.json`

---

## 📁 PROD/DEV/TEST Configs

Aktuell keine umgebungsspezifischen Configs.

Falls benötigt, können hier umgebungsspezifische Overrides abgelegt werden.

---

## 🗂️ Root Config Files

**Alembic Configs:**
- `alembic.ini` - Basis-Konfiguration
- `alembic-prod.ini` - PROD Database (seaser-postgres/rezepte)
- `alembic-test.ini` - TEST Database (seaser-postgres-test/rezepte_test)

**Pytest Config:**
- `pytest.ini` - Test-Konfiguration

**Hinweis:** Diese Configs bleiben im Root, da sie von Tools direkt geladen werden.

---

## 🔧 Config-Änderungen

### TheMealDB Strategy ändern

Bearbeite `config/shared/themealdb-config.json`:

```json
{
  "themealdb_import_config": {
    "default_strategy": "by_category",
    "preferences": {
      "favorite_categories": ["Vegetarian", "Dessert"]
    }
  }
}
```

### Migusto Preset hinzufügen

Bearbeite `config/shared/migusto-import-config.json`:

```json
{
  "migusto_import_config": {
    "presets": {
      "neues_preset": {
        "name": "Mein Preset",
        "filters": ["hauptgericht", "schnelleinfach"],
        "description": "Beschreibung"
      }
    }
  }
}
```

---

**Hinweis:** Nach Config-Änderungen Container neu bauen!

```bash
# PROD
./scripts/prod/deploy.sh <tag>

# DEV
./scripts/dev/build.sh
```
