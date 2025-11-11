# TEST Configuration

**Target:** TEST Container (seaser-rezept-tagebuch-test)

---

## Status

Aktuell keine TEST-spezifischen Config-Overrides.

Alle TEST Configs sind in `config/shared/`.

---

## Zukünftige Configs

Falls TEST-spezifische Overrides benötigt werden:

**Beispiel:** TEST-spezifische Config mit Mock-Data

```json
{
  "themealdb_import_config": {
    "api_base_url": "http://localhost:8001/mock-api",
    "default_strategy": "random"
  }
}
```

Dann in App Config-Loading diese Datei bevorzugen.
