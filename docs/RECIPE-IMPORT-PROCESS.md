# Recipe Import Process (BPMN)

TheMealDB Recipe Import Process - Business Process Model

**Version:** v25.11.06
**Stand:** November 2025

---

## Prozess-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                  THEMEALDB RECIPE IMPORT PROCESS                │
│                                                                 │
│  Trigger: systemd Timer (täglich 06:00 Uhr)                   │
│  Duration: ~10-15 Sekunden                                      │
│  Output: Importiertes & übersetztes Rezept in DB              │
└─────────────────────────────────────────────────────────────────┘
```

---

## BPMN Diagramm

### Prozess-Schritte

```
START (Timer 06:00)
  │
  ├─► [1] Load TheMealDB Config
  │        ├─ themealdb-config.json
  │        ├─ default_strategy
  │        └─ default_values
  │
  ├─► [2] Determine Import Strategy
  │        ├─ Query Parameter?
  │        └─ Config Default
  │
  ├─► [3] Gateway: Strategy Decision
  │        ├─► [3a] Fetch Random Recipe
  │        ├─► [3b] Fetch by Category (Vegetarian/Dessert)
  │        ├─► [3c] Fetch by Area (Italian/Indian/Thai)
  │        └─► [3d] Fetch by Ingredient (chicken/pasta)
  │
  ├─► [4] Gateway: Recipe Found?
  │        ├─ YES → Continue
  │        └─ NO  → END (Error)
  │
  ├─► [5] Download Recipe Image
  │        ├─ TheMealDB Image URL
  │        ├─ Generate UUID filename
  │        └─ Save to /data/uploads/
  │
  ├─► [6] Translate Title (EN → DE)
  │        └─ DeepL API
  │
  ├─► [7] Translate Instructions (EN → DE)
  │        └─ DeepL API
  │
  ├─► [8] Format Instructions
  │        ├─ Split by newlines
  │        ├─ Add SCHRITT 1, SCHRITT 2, ...
  │        └─ SCHRITT Parser Format
  │
  ├─► [9] Parse & Translate Ingredients
  │        ├─ Extract strIngredient1-20
  │        ├─ Extract strMeasure1-20
  │        ├─ Combine: "measure ingredient"
  │        └─ Translate each (DeepL API)
  │
  ├─► [10] Build Notes Structure
  │        ├─ SCHRITT sections
  │        ├─ "Zutaten:" section
  │        └─ Format with bullets
  │
  ├─► [11] Add Metadata
  │        ├─ Source: TheMealDB
  │        ├─ Original Title
  │        ├─ Category
  │        ├─ Area/Region
  │        └─ Translation Info
  │
  ├─► [12] Save Recipe to Database
  │        ├─ Table: recipes
  │        ├─ User: import@seaser.local (user_id=2)
  │        └─ Flag: auto_imported=1
  │
  ├─► [13] Cleanup Old Imports
  │        ├─ Find: auto_imported=1 AND imported_at < 7 days ago
  │        ├─ Check: No diary_entries linked
  │        └─ Delete: Recipe + Image
  │
  └─► END (Success)
```

---

## Prozess-Details

### Phase 1: Configuration & Strategy Selection

**Input:**
- `themealdb-config.json` (lokale Config)
- Query Parameter `strategy` (optional)
- Query Parameter `value` (optional)

**Logik:**
```python
strategy = request.args.get('strategy', config['default_strategy'])
value = request.args.get('value', None)

if not value and strategy.requires_parameter:
    value = random.choice(config.strategies[strategy].default_values)
```

**Output:**
- Selected Strategy: `by_category`, `by_area`, `random`, etc.
- Filter Value: `"Vegetarian"`, `"Italian"`, `"chicken"`, etc.

---

### Phase 2: Recipe Fetching

**API Calls:**

| Strategy | Endpoint | Example |
|----------|----------|---------|
| random | `random.php` | `https://themealdb.com/api/json/v1/1/random.php` |
| by_category | `filter.php?c=X` | `filter.php?c=Vegetarian` |
| by_area | `filter.php?a=X` | `filter.php?a=Italian` |
| by_ingredient | `filter.php?i=X` | `filter.php?i=chicken` |

**Special Handling:**
- Filter endpoints return ID list → Random selection → Fetch full recipe via `lookup.php?i={id}`

**Output:**
- Recipe JSON from TheMealDB
- Or `None` if not found

---

### Phase 3: Translation Pipeline

**DeepL API Integration:**

```python
def translate_to_german(text):
    response = requests.post(DEEPL_API_URL, data={
        'auth_key': DEEPL_API_KEY,
        'text': text,
        'source_lang': 'EN',
        'target_lang': 'DE'
    })
    return response.json()['translations'][0]['text']
```

**Translation Steps:**

1. **Title Translation**
   - Input: `"Sticky Toffee Pudding Ultimate"`
   - Output: `"Sticky Toffee Pudding Ultimate"` (DE)

2. **Instructions Translation**
   - Input: Full recipe text (EN)
   - Output: German translation
   - Format: Preserve line breaks

3. **Ingredients Translation** (20x)
   - Input: `"200g Plain flour"`
   - Output: `"200g Einfaches Mehl"`

---

### Phase 4: Parsing & Formatting

**SCHRITT Formatting:**

```
Original (EN):
"Preheat oven to 180C. Mix flour and sugar. Bake for 30 mins."

After Translation (DE):
"Ofen auf 180°C vorheizen. Mehl und Zucker mischen. 30 Min backen."

After Formatting:
SCHRITT 1

Ofen auf 180°C vorheizen. Mehl und Zucker mischen. 30 Min backen.
```

**Notes Structure:**
```
SCHRITT 1

[Anleitung Schritt 1]

SCHRITT 2

[Anleitung Schritt 2]

Zutaten:
- 200g Einfaches Mehl
- 100g Zucker
- 2 Eier

─────────────────────────
🌍 Quelle: TheMealDB
📖 Original: Sticky Toffee Pudding Ultimate
🏷️ Kategorie: Dessert
🌎 Region: British
🤖 Übersetzt mit DeepL
```

---

### Phase 5: Database Storage

**SQL Insert:**
```sql
INSERT INTO recipes (
    title,
    image,
    notes,
    user_id,
    auto_imported,
    imported_at,
    created_at,
    updated_at
) VALUES (
    'Sticky Toffee Pudding Ultimate',  -- translated_title
    'abc-123-def.jpg',                  -- image_filename
    '[SCHRITT + Zutaten + Metadata]',   -- formatted_notes
    2,                                   -- import user
    1,                                   -- auto_imported flag
    DATE('now'),                         -- import date
    CURRENT_TIMESTAMP,                   -- created
    CURRENT_TIMESTAMP                    -- updated
)
```

---

## Error Handling

### Fehlerszenarien

| Error | Ursache | Handling |
|-------|---------|----------|
| No recipe found | Filter returns empty list | Return 404, log warning |
| DeepL API Error | Rate limit, invalid key | Use original text, log error |
| Image download fails | Network error, 404 | Continue without image |
| Database error | Lock, constraint violation | Rollback, return 500 |

### Retry-Logik

**Aktuell:** Keine automatischen Retries

**Verhalten:**
- Bei Fehler: Import fehlgeschlagen
- Nächster Versuch: Nächster Tag 06:00 Uhr
- Manuell möglich: `curl -X POST .../daily-import`

---

## Performance Metriken

| Schritt | Duration | API Calls |
|---------|----------|-----------|
| Config Load | ~5ms | 0 |
| Strategy Selection | ~1ms | 0 |
| Recipe Fetch | ~500ms | 1-2 (filter + lookup) |
| Image Download | ~1-2s | 1 |
| Translation (Title) | ~200ms | 1 |
| Translation (Instructions) | ~500ms | 1 |
| Translation (Ingredients) | ~2-4s | 20 |
| Formatting | ~10ms | 0 |
| DB Save | ~50ms | 0 |
| Cleanup | ~100ms | 0 |
| **TOTAL** | **~5-10s** | **23-24** |

---

## Konfiguration

### themealdb-config.json

```json
{
  "default_strategy": "by_category",
  "strategies": {
    "by_category": {
      "endpoint": "filter.php",
      "parameter_key": "c",
      "default_values": ["Vegetarian", "Dessert"]
    }
  }
}
```

### systemd Service

```ini
[Service]
ExecStart=/usr/bin/curl -X POST \
  "http://localhost:8000/rezept-tagebuch/api/recipes/daily-import?strategy=by_category"
```

### systemd Timer

```ini
[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
```

---

## Monitoring

### Log-Ausgaben

```bash
# Service Logs
sudo journalctl -u rezept-daily-import.service -f

# Container Logs
podman logs --tail 50 seaser-rezept-tagebuch

# Success Pattern
"🔍 TheMealDB Import: strategy=by_category, c=Vegetarian"
"📖 Fetching full recipe details for ID 52772"
"✅ Recipe imported: ID 31"
```

### Erfolgs-Indikatoren

```bash
# Check last import
curl http://localhost:8000/rezept-tagebuch/api/recipes | jq '.[-1]'

# Count auto-imports
sqlite3 data/prod/rezepte.db "SELECT COUNT(*) FROM recipes WHERE auto_imported=1"

# Check today's import
sqlite3 data/prod/rezepte.db \
  "SELECT * FROM recipes WHERE auto_imported=1 AND imported_at=date('now')"
```

---

## Siehe auch

- **THEMEALDB-CONFIG.md** - Konfigurationsdetails
- **recipe-import-process.bpmn** - BPMN 2.0 XML
- **app.py:1004-1300** - Implementierung
- **test-recipe-import-e2e.sh** - E2E Test

---

**Erstellt:** 2025-11-06
**Format:** BPMN 2.0
**Tool:** Kann geöffnet werden mit: Camunda Modeler, bpmn.io, Visual Studio Code (BPMN Extension)
