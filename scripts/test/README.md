# TEST Environment Scripts

Scripts für die **Test-Umgebung** (seaser-rezept-tagebuch-test).

**Container:** seaser-rezept-tagebuch-test  
**Env Var:** `TESTING_MODE=true`

---

## Scripts

### build.sh
Baut TEST Container aus aktuellem Code.

---

### migration-workflow.sh
**Vollständiger Test-Workflow für PROD-Freigabe**

Workflow:
1. Baut TEST Container aus HEAD
2. Führt Alembic Migrationen aus
3. Führt Tests aus
4. Gibt Commit für PROD frei

---

### run-parallel-tests.sh
Führt Tests parallel aus.

