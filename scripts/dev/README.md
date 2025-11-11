# DEV Environment Scripts

Scripts für die **Development-Umgebung** (seaser-rezept-tagebuch-dev).

**Container:** seaser-rezept-tagebuch-dev  
**URL:** http://192.168.2.139:8000/rezept-tagebuch-dev/  
**Env Var:** `DEV_MODE=true`

---

## Scripts

### build.sh
Baut und startet den DEV Container neu.

```bash
./build.sh
```

---

### run-tests.sh
Führt pytest Test-Suite auf DEV Container aus.

```bash
./run-tests.sh
```

---

### run-tests-isolated.sh
Führt Tests isoliert aus.

---

### test-recipe-import-e2e.sh
End-to-End Test für Recipe-Import-Flow.

