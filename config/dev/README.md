# DEV Configuration

**Target:** DEV Container (seaser-rezept-tagebuch-dev)

---

## Status

Aktuell keine DEV-spezifischen Config-Overrides.

Alle DEV Configs sind in `config/shared/`.

---

## Zukünftige Configs

Falls DEV-spezifische Overrides benötigt werden:

**Beispiel:** DEV-spezifische Migusto Config mit reduzierten Limits

```json
{
  "migusto_import_config": {
    "max_recipes_per_import": 10,
    "delay_between_imports_ms": 500
  }
}
```

Dann in App Config-Loading diese Datei bevorzugen.
