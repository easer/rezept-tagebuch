# TheMealDB Import Konfiguration

Dokumentation für die konfigurierbare TheMealDB Import-Schnittstelle.

**Stand:** November 2025

---

## Überblick

Die Rezept-Tagebuch App importiert täglich Rezepte von [TheMealDB](https://www.themealdb.com/). Die Import-Strategie ist seit v25.11.06 voll konfigurierbar über `themealdb-config.json`.

### Unterstützte Import-Strategien

1. **random** - Zufälliges Rezept (default)
2. **by_category** - Nach Kategorie filtern (z.B. Vegetarian, Dessert, Seafood)
3. **by_area** - Nach Region/Küche filtern (z.B. Italian, Indian, Thai)
4. **by_ingredient** - Nach Hauptzutat filtern (z.B. chicken, pasta, salmon)
5. **by_first_letter** - Nach Anfangsbuchstabe suchen (a-z)
6. **by_name** - Nach Name suchen (benötigt Suchbegriff)

---

## Konfigurationsdatei

Die Konfiguration liegt in `themealdb-config.json` im Projektverzeichnis.

### Struktur

```json
{
  "themealdb_import_config": {
    "api_base_url": "https://www.themealdb.com/api/json/v1/1",
    "default_strategy": "random",
    "enabled_strategies": [...],
    "strategies": {
      "random": { ... },
      "by_category": { ... },
      "by_area": { ... },
      "by_ingredient": { ... }
    },
    "rotation": { ... },
    "preferences": { ... }
  }
}
```

### Wichtige Felder

#### `default_strategy`
Die Standard-Strategie wenn keine spezifische angegeben wird.

**Default:** `"random"`

#### `strategies`
Definition aller verfügbaren Import-Strategien mit:
- `endpoint` - TheMealDB API Endpoint
- `parameter_key` - Query Parameter (z.B. "c" für category)
- `requires_parameter` - Ob ein Wert erforderlich ist
- `available_values` - Liste erlaubter Werte
- `default_values` - Bevorzugte Werte (für Auto-Select)

#### `preferences`
Deine bevorzugten Kategorien, Regionen und Zutaten.

Wenn eine Strategie ohne expliziten Wert aufgerufen wird, wird zufällig aus diesen Listen gewählt.

**Beispiel:**
```json
"preferences": {
  "favorite_categories": ["Vegetarian", "Pasta", "Seafood"],
  "favorite_areas": ["Italian", "Indian", "Thai"],
  "favorite_ingredients": ["chicken", "pasta", "salmon"]
}
```

#### `rotation` (Geplant)
Ermöglicht automatische Rotation der Strategien nach Wochentag.

**Status:** Noch nicht implementiert (enabled: false)

---

## API Nutzung

### Endpoint

```
POST /api/recipes/daily-import
```

### Query Parameter

| Parameter | Typ | Beschreibung | Beispiel |
|-----------|-----|--------------|----------|
| `strategy` | string | Import-Strategie | `random`, `by_category`, `by_area` |
| `value` | string | Filter-Wert (optional) | `Vegetarian`, `Italian`, `chicken` |

### Beispiele

#### 1. Random Import (Default)

```bash
curl -X POST "http://localhost:8000/rezept-tagebuch-dev/api/recipes/daily-import"
```

**Response:**
```json
{
  "success": true,
  "recipe_id": 192,
  "title": "French Lentils With Garlic and Thyme",
  "title_de": "Französische Linsen mit Knoblauch und Thymian",
  "source": "TheMealDB",
  "strategy": "random",
  "filter_value": null,
  "category": "Miscellaneous",
  "area": "French",
  "imported_at": "2025-11-06"
}
```

#### 2. Nach Kategorie (Vegetarian)

```bash
curl -X POST "http://localhost:8000/rezept-tagebuch-dev/api/recipes/daily-import?strategy=by_category&value=Vegetarian"
```

**Response:**
```json
{
  "success": true,
  "strategy": "by_category",
  "filter_value": "Vegetarian",
  "category": "Vegetarian",
  ...
}
```

#### 3. Nach Region (Italienisch)

```bash
curl -X POST "http://localhost:8000/rezept-tagebuch-dev/api/recipes/daily-import?strategy=by_area&value=Italian"
```

#### 4. Nach Zutat (Chicken)

```bash
curl -X POST "http://localhost:8000/rezept-tagebuch-dev/api/recipes/daily-import?strategy=by_ingredient&value=chicken"
```

**Response:**
```json
{
  "success": true,
  "strategy": "by_ingredient",
  "filter_value": "chicken",
  "title": "Chicken Marengo",
  "category": "Chicken",
  ...
}
```

#### 5. Auto-Select aus Favoriten

Wenn `value` weggelassen wird, wählt das System zufällig aus den `default_values` bzw. `preferences`:

```bash
curl -X POST "http://localhost:8000/rezept-tagebuch-dev/api/recipes/daily-import?strategy=by_area"
```

Dies wählt zufällig aus: Italian, Indian, Chinese, Mexican, Thai

---

## Verfügbare Werte

### Kategorien (`by_category`)

- Beef
- Breakfast
- Chicken
- Dessert
- Goat
- Lamb
- Miscellaneous
- Pasta
- Pork
- Seafood
- Side
- Starter
- Vegan
- Vegetarian

### Regionen (`by_area`)

- American
- British
- Canadian
- Chinese
- Croatian
- Dutch
- Egyptian
- Filipino
- French
- Greek
- Indian
- Irish
- Italian
- Jamaican
- Japanese
- Kenyan
- Malaysian
- Mexican
- Moroccan
- Polish
- Portuguese
- Russian
- Spanish
- Thai
- Tunisian
- Turkish
- Ukrainian
- Vietnamese

### Zutaten (`by_ingredient`)

Beispiele (nicht vollständig):
- chicken, chicken_breast
- salmon, beef, pork
- pasta, rice
- tomato, potato, onion, garlic
- cheese, mushroom, spinach, broccoli, carrot

Vollständige Liste: https://www.themealdb.com/api/json/v1/1/list.php?i=list

---

## Konfiguration anpassen

### 1. Config-File bearbeiten

```bash
vim /home/gabor/easer_projekte/rezept-tagebuch/themealdb-config.json
```

### 2. Eigene Präferenzen setzen

Ändere die `preferences` Section:

```json
"preferences": {
  "favorite_categories": ["Vegan", "Vegetarian", "Breakfast"],
  "favorite_areas": ["Thai", "Indian", "Japanese"],
  "favorite_ingredients": ["tofu", "rice", "vegetables"]
}
```

### 3. Default-Strategie ändern

```json
"default_strategy": "by_category"
```

Jetzt wird standardmäßig nach Kategorie gefiltert (aus favorite_categories).

### 4. Container neu bauen

```bash
./scripts/deployment/build-dev.sh    # Für Dev
./scripts/deployment/deploy-prod.sh <TAG>  # Für Production
```

**Wichtig:** Config-Änderungen erfordern Container-Rebuild, da die Datei beim Build kopiert wird.

---

## Systemd Service anpassen

Der tägliche Import läuft via systemd Timer. Um die Strategie zu ändern:

### 1. Service-File bearbeiten

```bash
systemctl --user edit rezept-tagebuch-daily-import.service
```

### 2. Strategie-Parameter hinzufügen

```ini
[Service]
ExecStart=
ExecStart=/usr/bin/curl -X POST "http://localhost:8000/rezept-tagebuch/api/recipes/daily-import?strategy=by_area&value=Italian"
```

### 3. Service neu laden

```bash
systemctl --user daemon-reload
systemctl --user restart rezept-tagebuch-daily-import.timer
```

### 4. Nächste Ausführung prüfen

```bash
systemctl --user list-timers | grep rezept
```

---

## Troubleshooting

### Import schlägt fehl

**Symptom:** API gibt 404 oder 500 zurück

**Lösungen:**
1. Prüfe TheMealDB API Status: https://www.themealdb.com/
2. Prüfe Container Logs: `podman logs seaser-rezept-tagebuch-dev`
3. Teste API direkt: `curl "https://www.themealdb.com/api/json/v1/1/random.php"`

### Config wird nicht geladen

**Symptom:** Änderungen in Config haben keine Wirkung

**Lösung:** Container neu bauen:
```bash
./scripts/deployment/build-dev.sh
```

Die Config-Datei wird beim Build kopiert und muss bei Änderungen neu gebaut werden.

### Falsches Rezept importiert

**Hinweis:** TheMealDB's Filter-API gibt ALLE Rezepte zurück, die den Filter erfüllen, und wählt dann zufällig eines aus.

**Beispiel:**
- `strategy=by_category&value=Vegetarian`
- Gibt ALLE vegetarischen Rezepte zurück
- Wählt ZUFÄLLIG eines aus

Das ist **kein Bug**, sondern gewünschtes Verhalten für Vielfalt.

---

## API Referenz

### TheMealDB Endpoints

| Endpoint | Beschreibung | Beispiel |
|----------|--------------|----------|
| `/random.php` | Zufälliges Rezept | `random.php` |
| `/filter.php?c=X` | Filter nach Kategorie | `filter.php?c=Vegetarian` |
| `/filter.php?a=X` | Filter nach Region | `filter.php?a=Italian` |
| `/filter.php?i=X` | Filter nach Zutat | `filter.php?i=chicken` |
| `/search.php?s=X` | Suche nach Name | `search.php?s=Arrabiata` |
| `/search.php?f=X` | Suche nach Buchstabe | `search.php?f=a` |
| `/lookup.php?i=X` | Rezept nach ID | `lookup.php?i=52772` |

**Dokumentation:** https://www.themealdb.com/api.php

---

## Roadmap

### Geplante Features

1. **Rotation Schedule** ✅ Konfiguriert, ⏳ Implementierung pending
   - Automatische Strategie-Rotation nach Wochentag
   - Montag: Vegetarian, Dienstag: Italian, etc.

2. **Blacklist/Whitelist**
   - Bestimmte Zutaten ausschließen (z.B. Allergien)
   - Nur bestimmte Kategorien erlauben

3. **Smart Import**
   - Import basierend auf Tagebuch-Historie
   - Bevorzuge Rezepte ähnlich zu oft gekochten

4. **Multi-Import**
   - Mehrere Rezepte pro Tag importieren
   - User kann favorisieren

---

## Siehe auch

- **README.md** - Haupt-Dokumentation
- **DEPLOYMENT.md** - Deployment-Anleitung
- **recipe-format-config.json** - SCHRITT Parser Config

---

**Letzte Änderung:** 2025-11-06
