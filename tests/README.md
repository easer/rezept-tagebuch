# Rezept-Tagebuch Test Suite

Automatisierte Tests für die Rezept-Tagebuch API.

## 📋 Übersicht

Die Test-Suite besteht aus:
- **CRUD Tests** für Recipes (Create, Read, Update, Delete)
- **CRUD Tests** für Diary Entries
- **Integration Tests** für Parser und Search
- **E2E Tests** für Daily Import Flow

## 🚀 Tests ausführen

### Alle Tests

```bash
./run-tests.sh
```

### Spezifische Tests

```bash
# Nur Recipe Tests
./run-tests.sh tests/test_recipes_crud.py

# Nur Diary Tests
./run-tests.sh tests/test_diary_crud.py

# Einzelner Test
./run-tests.sh -k test_create_recipe_success

# Tests mit bestimmtem Marker
./run-tests.sh -m crud
```

### Test-Optionen

```bash
# Verbose Output
./run-tests.sh -v

# Stop bei erstem Fehler
./run-tests.sh -x

# Letzte fehlgeschlagene Tests
./run-tests.sh --lf

# Coverage Report
./run-tests.sh --cov=. --cov-report=html
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

### Dev-Container starten

Tests benötigen laufenden Dev-Container:

```bash
./build-dev.sh
```

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

## 🐛 Debugging

### Einzelnen Test debuggen

```bash
./run-tests.sh -k test_name -vv -s
```

`-vv` = sehr verbose
`-s` = print statements anzeigen

### Container-Logs prüfen

```bash
podman logs seaser-rezept-tagebuch-dev --tail 50
```

### Test mit pdb debuggen

In Test-Code einfügen:
```python
import pdb; pdb.set_trace()
```

Dann ausführen:
```bash
./run-tests.sh -k test_name -s
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
    ./build-dev.sh
    ./run-tests.sh --junitxml=test-results.xml
```

## 🔗 Siehe auch

- `../test-recipe-import-e2e.sh` - Shell-basierter E2E Test
- `../test-deepl.sh` - DeepL API Test
- `../README.md` - Haupt-Dokumentation
