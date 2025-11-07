# TheMealDB Import Konfiguration

Dokumentation für die konfigurierbare TheMealDB Import-Schnittstelle.

**Stand:** November 2025

---

## Überblick

Die Rezept-Tagebuch App importiert täglich Rezepte von [TheMealDB](https://www.themealdb.com/). Die Import-Strategie ist seit v25.11.06 voll konfigurierbar über `themealdb-config.json`.

**Wichtig:** Ab v25.11.07 ist ein **Meat-Filter** im Backend aktiv, der automatisch Fleisch-Rezepte ablehnt (Beef, Chicken, Lamb, Pork, Goat, Seafood). Das Wrapper-Script `daily-import.sh` wiederholt bei Ablehnung automatisch (bis zu 10 Versuche).

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

### Meat-Filter (Backend-Validierung)

**Seit v25.11.07** validiert das Backend die Kategorie vor dem Speichern:

**Erlaubte Kategorien:**
- Vegetarian, Vegan, Dessert, Breakfast, Pasta, Side, Starter, Miscellaneous

**Blockierte Kategorien (Fleisch):**
- Beef, Chicken, Lamb, Pork, Goat, Seafood

**Bei Ablehnung:**
- HTTP Status: `400 Bad Request`
- Response enthält `rejected_category` und `rejected_title`
- Wrapper-Script (`daily-import.sh`) wiederholt automatisch

**Code-Referenz:** `app.py` Zeilen 1180-1191

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

## Wrapper-Script mit Retry-Logik

### daily-import.sh

Seit v25.11.07 gibt es ein Wrapper-Script für robuste Imports mit automatischer Wiederholung bei Fleisch-Ablehnung.

**Location:** `/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh`

**Features:**
- Automatische Retry-Logik (bis zu 10 Versuche)
- 2 Sekunden Delay zwischen Versuchen
- Intelligente Fehlerbehandlung
- Logging für systemd journal
- Cleanup nach erfolgreichem Import

**Usage:**
```bash
daily-import.sh [strategy] [value]
```

**Beispiele:**
```bash
# Vegetarisches Rezept (Standard)
./scripts/daily-import.sh by_category Vegetarian

# Italienisches Rezept (mit Meat-Filter)
./scripts/daily-import.sh by_area Italian

# Zufälliges Rezept (nur fleischfrei)
./scripts/daily-import.sh random

# Dessert
./scripts/daily-import.sh by_category Dessert
```

**Ablauf bei Meat-Rejection:**
1. Script ruft API auf
2. Backend lehnt ab (HTTP 400): "Recipe rejected: 'Beef Wellington' (category: Beef)"
3. Script loggt Ablehnung
4. Wartet 2 Sekunden
5. Versucht es erneut (bis zu 10x)
6. Bei Erfolg: Cleanup und Exit 0
7. Nach 10 Versuchen: Exit 1 (Fehler)

**Log-Output (Beispiel):**
```
Starting daily recipe import (strategy: by_category, value: Vegetarian, max 10 attempts)...
Attempt 1/10: Fetching recipe...
⚠️ Recipe rejected: 'Chicken Tikka Masala' (category: Chicken)
Retrying in 2s...
Attempt 2/10: Fetching recipe...
✅ Success! Meat-free recipe imported.
Imported: Mushroom Risotto
Running cleanup of old imports...
✅ Daily import completed successfully
```

**Systemd Integration:**

Das Script wird vom systemd Service verwendet:
```ini
[Service]
Type=oneshot
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Vegetarian
StandardOutput=journal
StandardError=journal
```

**Monitoring:**
```bash
# Logs ansehen
journalctl --user -u rezept-daily-import.service --since today

# Live verfolgen
journalctl --user -u rezept-daily-import.service -f
```

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
vim /home/gabor/easer_projekte/rezept-tagebuch/config/themealdb-config.json
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

Der tägliche Import läuft via systemd Timer mit dem `daily-import.sh` Wrapper-Script.

**Aktueller Service:** Täglich um 06:00 UTC, Vegetarian

### 1. Service-File bearbeiten

```bash
vim ~/.config/systemd/user/rezept-daily-import.service
```

### 2. Strategie-Parameter ändern

**Option A: Italienische Rezepte**
```ini
[Service]
Type=oneshot
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_area Italian
StandardOutput=journal
StandardError=journal
```

**Option B: Desserts**
```ini
[Service]
Type=oneshot
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Dessert
StandardOutput=journal
StandardError=journal
```

**Option C: Random (nur fleischfrei)**
```ini
[Service]
Type=oneshot
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh random
StandardOutput=journal
StandardError=journal
```

### 3. Service neu laden

```bash
systemctl --user daemon-reload
systemctl --user restart rezept-daily-import.timer
```

### 4. Testen

```bash
# Manuell triggern
systemctl --user start rezept-daily-import.service

# Logs ansehen
journalctl --user -u rezept-daily-import.service --since "5 minutes ago"
```

### 5. Nächste Ausführung prüfen

```bash
systemctl --user list-timers | grep rezept
```

### Zusätzliche Services erstellen

Du kannst mehrere Timer für verschiedene Strategien haben. Siehe `systemd/README.md` für Details.

**Beispiel:**
- Montag-Freitag 06:00: Vegetarian (Haupt-Service)
- Mittwoch + Samstag 12:00: Italian (Zusatz-Service)
- Sonntag 18:00: Dessert (Zusatz-Service)

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

### Fleisch-Rezept wurde importiert (sollte nicht passieren)

**Symptom:** Ein Rezept mit Beef/Chicken/etc wurde trotz Meat-Filter importiert

**Check:**
1. Prüfe Backend-Code: `app.py` Zeilen 1180-1191
2. Prüfe ob Wrapper-Script verwendet wird: `systemctl --user cat rezept-daily-import.service`
3. Prüfe Logs: `journalctl --user -u rezept-daily-import.service --since today`

**Mögliche Ursachen:**
- Service nutzt noch alten curl-Befehl statt Wrapper-Script
- Backend-Filter wurde deaktiviert
- TheMealDB hat falsche Kategorie-Klassifizierung

### Import schlägt nach 10 Versuchen fehl

**Symptom:** Script gibt nach 10 Versuchen auf

**Ursache:** Bei `random` Strategie kann es vorkommen, dass 10x hintereinander Fleisch-Rezepte gezogen werden (unwahrscheinlich, aber möglich)

**Lösung:**
```bash
# Wechsel zu gezielter Strategie
vim ~/.config/systemd/user/rezept-daily-import.service

# Ändere zu:
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Vegetarian
```

Dann:
```bash
systemctl --user daemon-reload
systemctl --user restart rezept-daily-import.timer
```

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
