# PROD Automation Scripts

Automatisierte Scripts für die PROD-Umgebung (läuft auf dem Host via Cron).

## Daily Import Scripts

### daily-import-themealdb.sh
Täglicher automatischer Import von TheMealDB-Rezepten.

**Target:** PROD Container (localhost:8000/rezept-tagebuch)

**Features:**
- Retry-Logik (max 10 Versuche)
- Filtert Fleisch-Rezepte automatisch aus
- Cleanup alter Auto-Imports (>30 Tage)

**Usage:**
```bash
# Mit Standard-Strategie (vegetarisch)
./daily-import-themealdb.sh

# Mit Custom-Strategie
./daily-import-themealdb.sh by_category Vegetarian
./daily-import-themealdb.sh by_area Italian
./daily-import-themealdb.sh random
```

**Cron Setup:**
```bash
# Täglich um 6:00 Uhr
0 6 * * * /home/gabor/easer_projekte/rezept-tagebuch/scripts/automation/prod/daily-import-themealdb.sh
```

---

### daily-import-migusto.sh
Täglicher automatischer Import von Migusto-Rezepten.

**Target:** PROD Container (localhost:8000/rezept-tagebuch)

**Features:**
- Nutzt vordefinierte Presets aus config
- Zufälliges Preset wenn kein Parameter
- Cleanup alter Auto-Imports (>30 Tage)

**Presets:**
- `vegetarische_pasta_familie`
- `vegane_hauptgerichte`
- `schnelle_familiengerichte`

**Usage:**
```bash
# Zufälliges Preset
./daily-import-migusto.sh

# Spezifisches Preset
./daily-import-migusto.sh vegetarische_pasta_familie
```

**Cron Setup:**
```bash
# Täglich um 7:00 Uhr
0 7 * * * /home/gabor/easer_projekte/rezept-tagebuch/scripts/automation/prod/daily-import-migusto.sh
```

---

## Cron-Integration

Diese Scripts sind für automatische tägliche Ausführung auf dem Host gedacht.

**Installation:**
```bash
# Cron-Jobs installieren
./scripts/setup/install-daily-import.sh
```

**Manuelles Setup:**
```bash
crontab -e

# TheMealDB Import täglich um 6:00
0 6 * * * /home/gabor/easer_projekte/rezept-tagebuch/scripts/automation/prod/daily-import-themealdb.sh >> /var/log/rezept-import.log 2>&1

# Migusto Import täglich um 7:00
0 7 * * * /home/gabor/easer_projekte/rezept-tagebuch/scripts/automation/prod/daily-import-migusto.sh >> /var/log/rezept-import.log 2>&1
```

---

**Hinweis:** Diese Scripts greifen auf PROD zu (localhost:8000). Stelle sicher, dass der PROD Container läuft!
