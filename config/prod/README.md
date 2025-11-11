# PROD Configuration

**Target:** PROD Container (seaser-rezept-tagebuch)

---

## Status

Aktuell keine PROD-spezifischen Config-Overrides.

Alle PROD Configs sind in `config/shared/`.

---

## Zukünftige Configs

Falls PROD-spezifische Overrides benötigt werden:

**Beispiel:** PROD-spezifische TheMealDB Strategy

```json
{
  "themealdb_import_config": {
    "default_strategy": "by_category",
    "preferences": {
      "favorite_categories": ["Vegetarian"]
    }
  }
}
```

Dann in App Config-Loading diese Datei bevorzugen.
