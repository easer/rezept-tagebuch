# Rezept-Tagebuch Test Suite

Automatisierte Tests für die Rezept-Tagebuch API.

## 📋 Übersicht

Die Test-Suite besteht aus:
- **CRUD Tests** für Recipes (Create, Read, Update, Delete)
- **CRUD Tests** für Diary Entries
- **Integration Tests** für Parser und Search
- **E2E Tests** für Daily Import Flow

## 🚀 Tests ausführen

### Standard: Mit Dev-Datenbank

```bash
./scripts/testing/run-tests.sh
```

**Hinweis**: Tests nutzen PostgreSQL Test-Datenbank (`seaser-postgres-test:rezepte_test`) - komplett isoliert von Dev und Prod.

### On-Demand Test-Container

Der Test-Container startet **automatisch** wenn pytest läuft:

```bash
pytest tests/
# 🚀 Starting test container seaser-rezept-tagebuch-test...
# ✅ 27 passed in 15.70s
# 🧹 Stopping test container...
```

Container wird nach Tests automatisch gestoppt (außer er lief bereits vorher).

### Empfohlen: Mit isolierter Test-Datenbank

```bash
./scripts/testing/run-tests-isolated.sh
```

Startet Container im TESTING_MODE mit separater PostgreSQL Test-DB.

### Spezifische Tests

```bash
# Nur Recipe Tests
./scripts/testing/run-tests.sh tests/test_recipes_crud.py

# Nur Diary Tests
./scripts/testing/run-tests.sh tests/test_diary_crud.py

# Einzelner Test
./scripts/testing/run-tests.sh -k test_create_recipe_success

# Tests mit bestimmtem Marker
./scripts/testing/run-tests.sh -m crud

# Isoliert mit spezifischen Tests
./scripts/testing/run-tests-isolated.sh tests/test_recipes_crud.py -v
```

### Test-Optionen

```bash
# Verbose Output
./scripts/testing/run-tests.sh -v

# Stop bei erstem Fehler
./scripts/testing/run-tests.sh -x

# Letzte fehlgeschlagene Tests
./scripts/testing/run-tests.sh --lf

# Coverage Report
./scripts/testing/run-tests.sh --cov=. --cov-report=html
```

## 📁 Test-Struktur

```
tests/
├── __init__.py              # Test Package
├── conftest.py              # Pytest Fixtures & Config
├── test_recipes_crud.py     # Recipe CRUD Tests
├── test_diary_crud.py       # Diary CRUD Tests
└── README.md                # Diese Datei
```

## 🔧 Setup

### Requirements installieren

```bash
pip3 install -r requirements.txt
```

**Requirements:**
- pytest==7.4.4
- pytest-timeout==2.2.0
- requests==2.31.0

### Test-Container (automatisch)

Der Test-Container startet **automatisch** wenn pytest läuft - kein manuelles Setup nötig!

**Optional:** Container manuell starten (für Debugging):

```bash
./scripts/deployment/build-test.sh
```

Der Container bleibt dann nach Tests laufen.

## 📝 Test-Beschreibungen

### Recipe CRUD Tests (`test_recipes_crud.py`)

**TestRecipeCreate:**
- `test_create_recipe_success` - Recipe erstellen
- `test_create_recipe_missing_title` - Validierung: Titel erforderlich
- `test_create_recipe_with_image` - Recipe mit Bild-Upload

**TestRecipeRead:**
- `test_get_recipe_by_id` - Recipe abrufen
- `test_get_recipe_not_found` - 404 für nicht existierende ID
- `test_list_recipes` - Alle Recipes auflisten

**TestRecipeUpdate:**
- `test_update_recipe_title` - Titel aktualisieren
- `test_update_recipe_rating` - Rating aktualisieren
- `test_update_recipe_not_found` - 404 für Update

**TestRecipeDelete:**
- `test_delete_recipe_success` - Recipe löschen
- `test_delete_recipe_not_found` - 404 für Löschen

**TestRecipeSearch:**
- `test_search_recipes_by_title` - Suche nach Titel
- `test_search_recipes_empty_query` - Leere Suche

**TestRecipeParser:**
- `test_recipe_with_schritt_format` - SCHRITT-Formatting Validierung

### Diary CRUD Tests (`test_diary_crud.py`)

**TestDiaryCreate:**
- `test_create_diary_entry_success` - Diary Entry erstellen
- `test_create_diary_entry_missing_title` - Validierung: Titel erforderlich
- `test_create_diary_entry_with_recipe_link` - Entry mit Recipe-Link

**TestDiaryRead:**
- `test_get_diary_entry_by_id` - Entry abrufen
- `test_get_diary_entry_not_found` - 404 für nicht existierende ID
- `test_list_diary_entries` - Alle Entries auflisten

**TestDiaryUpdate:**
- `test_update_diary_entry_title` - Titel aktualisieren
- `test_update_diary_entry_content` - Content aktualisieren
- `test_update_diary_entry_not_found` - 404 für Update

**TestDiaryDelete:**
- `test_delete_diary_entry_success` - Entry löschen
- `test_delete_diary_entry_not_found` - 404 für Löschen

**TestDiarySearch:**
- `test_search_diary_entries_by_title` - Suche nach Titel
- `test_search_diary_entries_by_content` - Suche nach Content

## 🛠️ Fixtures

### `api_client`
HTTP Client für API-Requests (GET, POST, PUT, DELETE)

### `cleanup_test_recipes`
Automatisches Cleanup von Test-Recipes nach Test-Ende

### `cleanup_test_diary_entries`
Automatisches Cleanup von Test-Diary-Entries nach Test-Ende

### `sample_recipe_data`
Beispiel-Daten für Recipe-Tests

### `sample_diary_entry_data`
Beispiel-Daten für Diary-Entry-Tests

## 🎯 Test-Umgebung

### PostgreSQL Test-Datenbank

Tests laufen gegen eine **komplett isolierte** PostgreSQL-Datenbank:

- **Container**: `seaser-postgres-test`
- **Datenbank**: `rezepte_test`
- **Isolation**: Keine Interferenz mit PROD/DEV
- **Performance**: Parallele Tests ohne Locks (pytest-xdist)

### Container Lifecycle

**Automatisch (Standard)**:
```bash
pytest tests/
# Container startet → Tests laufen → Container stoppt
```

**Manuell (für Debugging)**:
```bash
./scripts/deployment/build-test.sh
pytest tests/
# Container bleibt laufen für weitere Tests/Debugging
podman stop seaser-rezept-tagebuch-test  # Manuell stoppen
```

## 🐛 Debugging

### Einzelnen Test debuggen

```bash
./scripts/testing/run-tests.sh -k test_name -vv -s
```

`-vv` = sehr verbose
`-s` = print statements anzeigen

### Container-Logs prüfen

```bash
podman logs seaser-rezept-tagebuch-test --tail 50
```

### Test-Datenbank inspizieren (PostgreSQL)

```bash
# psql Shell
podman exec -it seaser-postgres-test psql -U postgres -d rezepte_test

# Beispiel-Abfragen
\dt  # Alle Tabellen
SELECT * FROM recipes;
SELECT * FROM diary_entries;
```

### Test mit pdb debuggen

In Test-Code einfügen:
```python
import pdb; pdb.set_trace()
```

Dann ausführen:
```bash
./scripts/testing/run-tests.sh -k test_name -s
```

## ✅ Best Practices

1. **Cleanup verwenden**: Immer `cleanup_test_recipes` oder `cleanup_test_diary_entries` Fixtures nutzen
2. **Eindeutige Namen**: Test-Daten mit eindeutigen Namen (z.B. "Test Recipe pytest")
3. **Unabhängige Tests**: Jeder Test soll unabhängig laufen können
4. **Assertions**: Klare, spezifische Assertions mit Fehlermeldungen
5. **Timeout**: Tests sollten schnell sein (< 5 Sekunden)

## 📊 CI/CD Integration

Tests können in CI/CD Pipeline integriert werden:

```bash
# Beispiel für GitHub Actions
- name: Run Tests
  run: |
    ./scripts/deployment/build-dev.sh
    ./scripts/testing/run-tests.sh --junitxml=test-results.xml
```

## 🔗 Siehe auch

- `../scripts/testing/test-recipe-import-e2e.sh` - Shell-basierter E2E Test
- `../scripts/testing/test-deepl.sh` - DeepL API Test
- `../README.md` - Haupt-Dokumentation
