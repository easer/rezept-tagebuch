# TEST Environment Scripts

Scripts für die **Test-Umgebung** (seaser-rezept-tagebuch-test).

**Container:** seaser-rezept-tagebuch-test  
**Port:** 8001  
**Env Var:** `TESTING_MODE=true`  
**Database:** PostgreSQL rezepte_test

---

## Scripts

### build.sh
Baut TEST Container aus aktuellem Code.

```bash
./build.sh
```

**Was passiert:**
1. Baut Image: `seaser-rezept-tagebuch:test`
2. Stoppt alten TEST Container
3. Startet neuen Container mit `TESTING_MODE=true`
4. Verbindet mit PostgreSQL: `seaser-postgres-test` / `rezepte_test`

---

### test-and-approve-for-prod.sh
**Vollständiger Test-Workflow für PROD-Freigabe**

```bash
./test-and-approve-for-prod.sh
```

**Workflow:**
1. ✅ Prüft ob Working Directory clean ist
2. ✅ Baut TEST Container aus HEAD (git archive)
3. ✅ Startet TEST Container
4. ✅ Führt Alembic Migrationen auf PostgreSQL aus
5. ✅ Führt pytest Tests aus
6. ✅ Gibt Commit für PROD frei (`.test-approvals`)
7. ✅ Optional: DEV Container aktualisieren

**Wichtig:** Nur erfolgreich getestete Commits können auf PROD deployed werden!

---

### run-tests.sh
Führt pytest Test-Suite auf TEST Container aus.

```bash
./run-tests.sh          # Alle Tests
./run-tests.sh -k test  # Spezifischer Test
```

**Was wird getestet:**
- API Endpoints (CRUD Operations)
- Recipe Parser
- Database Operations (PostgreSQL)
- Import Workflows

**Testet gegen:** TEST Container (localhost:8001)

**Voraussetzung:** TEST Container muss laufen

---

### run-parallel-tests.sh
Führt Tests parallel aus (schnellere Ausführung).

```bash
./run-parallel-tests.sh
```

**Use Case:** CI/CD, schnelle Test-Ausführung

**Testet gegen:** TEST Container

---

### run-performance-tests.sh
Führt Performance-Tests für Recipe-Imports aus.

```bash
./run-performance-tests.sh
```

**Was wird getestet:**
- TheMealDB Import: < 3 Sekunden
- Migusto Import: < 3 Sekunden

**Use Case:** Performance-Regression Detection

**Voraussetzung:** TEST Container muss laufen

---

**Target:** TEST Container (seaser-rezept-tagebuch-test)
