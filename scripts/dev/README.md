# DEV Environment Scripts

Scripts für die **Development-Umgebung** (seaser-rezept-tagebuch-dev).

**Container:** seaser-rezept-tagebuch-dev  
**URL:** http://192.168.2.139:8000/rezept-tagebuch-dev/  
**Env Var:** `DEV_MODE=true`  
**Database:** PostgreSQL rezepte_dev

---

## Scripts

### build.sh
Baut und startet den DEV Container neu.

```bash
./build.sh
```

**Was passiert:**
1. Baut Image: `seaser-rezept-tagebuch:dev`
2. Stoppt alten Container
3. Startet neuen Container mit `DEV_MODE=true`
4. Mounted: `data/dev/uploads`
5. Verbindet mit PostgreSQL: `seaser-postgres-dev` / `rezepte_dev`

---

### test-recipe-import-e2e.sh
End-to-End Test für kompletten Recipe-Import-Flow.

```bash
./test-recipe-import-e2e.sh
```

**Was wird getestet:**
- TheMealDB API Integration
- DeepL Translation (DE→DE Übersetzung)
- SCHRITT Formatting
- DB Storage (PostgreSQL)
- Recipe Parser
- Cleanup alter Auto-Imports

**Testet gegen:** DEV Container (localhost:8000/rezept-tagebuch-dev)

**Voraussetzung:** 
- DEV Container muss laufen
- `DEEPL_API_KEY` in .env

---

**Target:** DEV Container (seaser-rezept-tagebuch-dev)
