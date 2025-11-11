# PROD Security Analysis - Tag & Database Protection

**Datum:** 2025-11-11
**Status:** ⚠️ PROD läuft aktuell mit `latest` Tag (UNSICHER)

---

## 🔴 AKTUELLE PROBLEME

### Problem 1: PROD Container verwendet `latest` statt Version-Tag

**IST-Zustand:**
```bash
# PROD Container
Image: localhost/seaser-rezept-tagebuch:latest
APP_VERSION=latest
```

**Risiken:**
- ❌ Kein Rollback möglich (welche Version läuft gerade?)
- ❌ Keine Nachvollziehbarkeit (welcher Code ist deployed?)
- ❌ `latest` kann sich jederzeit ändern
- ❌ Neustart des Containers könnte andere Version laden

**SOLL-Zustand:**
```bash
# PROD Container sollte verwenden:
Image: localhost/seaser-rezept-tagebuch:rezept_version_10_11_2025_002
APP_VERSION=rezept_version_10_11_2025_002
```

---

### Problem 2: Keine Absicherung gegen falsche Datenbank

**IST-Zustand:**
```bash
# PROD Container nutzt korrekt:
postgresql://postgres:seaser@seaser-postgres/rezepte

# ABER: Keine Prüfung dass nicht versehentlich:
# - rezepte_test (TEST DB)
# - rezepte_dev (DEV DB)
# verwendet wird!
```

**Risiken:**
- ❌ Versehentliches Deployment auf TEST-DB würde PROD-Daten zerstören
- ❌ Kein Safety-Check vor Migration
- ❌ Alembic könnte auf falsche DB zeigen

---

### Problem 3: Systemd Service hat hardcoded `latest`

**IST-Zustand:**
```bash
# /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service
ExecStart=/usr/bin/podman run ... localhost/seaser-rezept-tagebuch:latest
```

**Problem:**
- Service wird bei `systemctl restart` automatisch mit `latest` gestartet
- Selbst wenn manuell ein Tag verwendet wird, überschreibt systemd das

---

### Problem 4: 24 Commits nicht auf PROD deployed

**IST-Zustand:**
```bash
# Letzter PROD Tag: rezept_version_10_11_2025_002 (1a974cf)
# HEAD: e0ba6c9 (24 Commits voraus)
```

**Commits seit letztem Tag:**
- Performance-Optimierung (Batch Translation)
- Performance-Tests
- Migusto Daily Import Fix
- Dokumentation Updates
- **NICHT auf PROD deployed!**

---

## ✅ LÖSUNGSKONZEPT

### Lösung 1: Tag-basiertes Deployment erzwingen

#### 1.1 Deploy-Script bereits korrekt

Das `scripts/prod/deploy.sh` ist bereits gut:
- ✅ Erzwingt Git-Tag als Parameter
- ✅ Validiert Tag-Format: `rezept_version_DD_MM_YYYY_NNN`
- ✅ Prüft Test-Approval aus `.test-approvals`
- ✅ Baut Image mit Tag
- ✅ Setzt `APP_VERSION=$GIT_TAG` im Container

**ABER:**
- ❌ Zeile 148: Taggt Image als `latest` (PROBLEM!)
- ❌ Zeile 182: Verwendet `localhost/seaser-rezept-tagebuch:latest` (PROBLEM!)

#### 1.2 Empfohlene Änderungen

**deploy.sh Zeile 145-182 ändern:**
```bash
# VORHER (UNSICHER):
podman tag seaser-rezept-tagebuch:$GIT_TAG seaser-rezept-tagebuch:latest
podman run -d ... localhost/seaser-rezept-tagebuch:latest

# NACHHER (SICHER):
# KEIN latest-Tag mehr!
podman run -d ... localhost/seaser-rezept-tagebuch:$GIT_TAG
```

**Systemd Service generieren mit Tag:**
```bash
# deploy.sh Zeile 187 ändern:
podman generate systemd --new --name seaser-rezept-tagebuch > \
  /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service

# Problem: --name findet laufenden Container, der hardcoded "latest" hat
# Lösung: Vor generate systemd den Tag im Service-File anpassen
```

---

### Lösung 2: Database Safety Checks

#### 2.1 Startup-Validierung im Container

**Neues Script:** `scripts/prod/validate-prod-environment.sh`

```bash
#!/bin/bash
# PROD Environment Validation
# Runs at container startup to ensure correct configuration

set -e

echo "🔒 PROD Environment Validation..."

# 1. Check APP_VERSION is NOT "latest"
if [ "$APP_VERSION" = "latest" ] || [ -z "$APP_VERSION" ]; then
    echo "❌ ERROR: APP_VERSION must be a version tag, not 'latest'!"
    echo "   Expected: rezept_version_DD_MM_YYYY_NNN"
    echo "   Got: ${APP_VERSION:-<not set>}"
    exit 1
fi

# 2. Check database is PROD database
DB_URL=$(grep "^sqlalchemy.url" /app/alembic.ini | cut -d'=' -f2 | xargs)
EXPECTED_DB="postgresql://postgres:seaser@seaser-postgres/rezepte"

if [ "$DB_URL" != "$EXPECTED_DB" ]; then
    echo "❌ ERROR: Wrong database configured!"
    echo "   Expected: $EXPECTED_DB"
    echo "   Got: $DB_URL"
    echo ""
    echo "   DANGER: This could destroy PROD data!"
    exit 1
fi

# 3. Check TESTING_MODE is NOT set
if [ -n "$TESTING_MODE" ]; then
    echo "❌ ERROR: TESTING_MODE is set on PROD!"
    echo "   This container is configured for testing, not production."
    exit 1
fi

# 4. Verify network is correct
NETWORK=$(hostname -I | xargs)
if [[ ! "$NETWORK" =~ ^10\.89\.0\. ]]; then
    echo "⚠️  WARNING: Not on seaser-network (10.89.0.0/24)"
    echo "   IP: $NETWORK"
fi

echo "✅ PROD Environment validated successfully"
echo "   Version: $APP_VERSION"
echo "   Database: rezepte (PROD)"
echo "   Network: $NETWORK"
```

**Integration in Containerfile:**
```dockerfile
# Add validation script
COPY scripts/prod/validate-prod-environment.sh /usr/local/bin/

# Run validation before starting app
CMD ["/bin/bash", "-c", "validate-prod-environment.sh && gunicorn ..."]
```

#### 2.2 Pre-Deployment Database Check

**deploy.sh erweitern (vor Migration):**

```bash
echo "🔒 Step 1.5/6: Validating database connection..."

# Read DB URL from alembic-prod.ini
DB_URL=$(grep "^sqlalchemy.url" "$TEMP_DIR/alembic-prod.ini" | cut -d'=' -f2 | xargs)
EXPECTED_DB="postgresql://postgres:seaser@seaser-postgres/rezepte"

if [ "$DB_URL" != "$EXPECTED_DB" ]; then
    echo -e "${RED}❌ DANGER: Wrong database in alembic-prod.ini!${NC}"
    echo "   Expected: $EXPECTED_DB"
    echo "   Got: $DB_URL"
    echo ""
    echo "   This would destroy PROD data! Aborting."
    exit 1
fi

# Verify database is reachable and is PROD
DB_CHECK=$(podman exec seaser-postgres psql -U postgres -d rezepte -tAc "SELECT COUNT(*) FROM recipes WHERE auto_imported=false" 2>/dev/null || echo "ERROR")

if [ "$DB_CHECK" = "ERROR" ]; then
    echo -e "${RED}❌ Cannot connect to PROD database!${NC}"
    exit 1
fi

echo "✅ Database validated: rezepte (PROD) - $DB_CHECK user recipes"
```

---

### Lösung 3: Rollback-Sicherheit

#### 3.1 Rollback-Script validieren

**rollback.sh prüfen:**
```bash
# Sollte NICHT latest verwenden
# Sollte NUR auf getaggte Versionen zurückrollen
```

#### 3.2 Emergency Rollback ohne latest

```bash
#!/bin/bash
# emergency-rollback.sh
# Rollt auf letzten bekannten guten Tag zurück

LAST_GOOD_TAG=$(git tag | grep "^rezept_version_" | tail -1)

echo "🚨 Emergency Rollback to: $LAST_GOOD_TAG"
./scripts/prod/deploy.sh "$LAST_GOOD_TAG"
```

---

### Lösung 4: Test-Approval-Pflicht verschärfen

#### 4.1 Approval-File Format erweitern

```bash
# .test-approvals Format:
COMMIT_HASH|TIMESTAMP|STATUS|COMMIT_MSG|TESTS_PASSED|PERFORMANCE_OK

# Neue Felder:
# - TESTS_PASSED: Anzahl bestandener Tests
# - PERFORMANCE_OK: true/false (TheMealDB < 3s, Migusto < 3s)
```

#### 4.2 Deploy-Script prüft Performance-Tests

```bash
# deploy.sh erweitern:
APPROVAL_LINE=$(grep "^$TAG_COMMIT_HASH|" "$APPROVAL_FILE" | tail -1)
PERFORMANCE_OK=$(echo "$APPROVAL_LINE" | cut -d'|' -f6)

if [ "$PERFORMANCE_OK" != "true" ]; then
    echo -e "${RED}❌ Performance-Tests nicht bestanden!${NC}"
    echo "   Tag kann nicht auf PROD deployed werden."
    exit 1
fi
```

---

## 🎯 IMPLEMENTIERUNGSPLAN

### Phase 1: Sofort-Maßnahmen (High Priority)

1. **Deploy-Script absichern:**
   - ❌ `latest` Tag nicht mehr erstellen
   - ✅ Nur versionierte Tags verwenden
   - ✅ Database-Check vor Migration

2. **Container-Validierung:**
   - ✅ `validate-prod-environment.sh` erstellen
   - ✅ In Containerfile integrieren
   - ✅ APP_VERSION != "latest" prüfen

3. **Aktuellen Stand taggen:**
   - ✅ HEAD committen
   - ✅ Auf TEST testen
   - ✅ Tag erstellen: `rezept_version_11_11_2025_001`
   - ✅ Auf PROD deployen (mit neuem sicheren Script)

### Phase 2: Erweiterte Absicherung (Medium Priority)

4. **Test-Approval erweitern:**
   - ✅ Performance-Tests in Approval aufnehmen
   - ✅ Deploy-Script prüft Performance-OK

5. **Monitoring:**
   - ✅ Logging: Welche Version läuft auf PROD
   - ✅ Alert: Wenn APP_VERSION=latest

6. **Dokumentation:**
   - ✅ DEPLOYMENT.md aktualisieren
   - ✅ Prozess dokumentieren

### Phase 3: Automatisierung (Low Priority)

7. **CI/CD Pipeline:**
   - Auto-Tag bei Merge to main
   - Auto-Test auf TEST
   - Manual Approval für PROD

---

## 📋 CHECKLISTE: Sicheres PROD Deployment

Vor jedem PROD Deployment:

- [ ] Working Directory clean (`git status`)
- [ ] Alle Änderungen committed
- [ ] Tests auf TEST bestanden
- [ ] Performance-Tests < 3s
- [ ] Commit in `.test-approvals` freigegeben
- [ ] Git-Tag erstellt: `rezept_version_DD_MM_YYYY_NNN`
- [ ] Tag-Format validiert
- [ ] Database-Backup existiert
- [ ] alembic-prod.ini zeigt auf `rezepte` (nicht rezepte_test!)
- [ ] Deploy-Script verwendet TAG (nicht latest)
- [ ] APP_VERSION im Container = Tag
- [ ] Systemd Service verwendet TAG
- [ ] Rollback-Plan vorhanden

---

## 🔧 KONKRETE ÄNDERUNGEN NÖTIG

### Datei: `scripts/prod/deploy.sh`

**Zeilen ändern:**

```bash
# Zeile 145-148: ENTFERNEN
# VORHER:
echo ""
echo "🏷️  Step 3/6: Tagging as latest..."
podman tag seaser-rezept-tagebuch:$GIT_TAG seaser-rezept-tagebuch:latest

# NACHHER:
# REMOVED: No latest tag for security

# Zeile 182: ÄNDERN
# VORHER:
  localhost/seaser-rezept-tagebuch:latest

# NACHHER:
  localhost/seaser-rezept-tagebuch:$GIT_TAG

# Zeile 187: ÄNDERN
# VORHER:
podman generate systemd --new --name seaser-rezept-tagebuch > ...

# NACHHER:
# Generate systemd with specific tag
podman generate systemd --new seaser-rezept-tagebuch > \
  /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service

# Fix hardcoded latest in systemd file
sed -i "s|localhost/seaser-rezept-tagebuch:latest|localhost/seaser-rezept-tagebuch:$GIT_TAG|g" \
  /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service
```

**Neue Validierung einfügen (nach Zeile 138):**

```bash
# Step 1.5: Validate database configuration
echo "🔒 Step 1.5/7: Validating database configuration..."
DB_URL=$(grep "^sqlalchemy.url" "$TEMP_DIR/alembic-prod.ini" | cut -d'=' -f2 | xargs)
EXPECTED_DB="postgresql://postgres:seaser@seaser-postgres/rezepte"

if [ "$DB_URL" != "$EXPECTED_DB" ]; then
    echo -e "${RED}❌ FATAL: Wrong database in alembic-prod.ini!${NC}"
    echo "   Expected: $EXPECTED_DB"
    echo "   Got: $DB_URL"
    echo ""
    echo "   Deployment would target wrong database!"
    echo "   This could destroy PROD data!"
    exit 1
fi

echo "✅ Database configuration validated: rezepte (PROD)"
echo ""
```

---

### Datei: `container/Containerfile`

**Neue Zeilen einfügen (vor CMD):**

```dockerfile
# Add PROD validation script
COPY scripts/prod/validate-prod-environment.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/validate-prod-environment.sh

# Validate environment on startup (PROD only)
# Will exit with error if:
# - APP_VERSION is "latest" or unset
# - Database is not "rezepte"
# - TESTING_MODE is set
ENV VALIDATE_PROD=true

# Modified CMD with validation
CMD ["/bin/bash", "-c", "if [ \"$VALIDATE_PROD\" = \"true\" ]; then validate-prod-environment.sh; fi && gunicorn --workers 4 --bind 0.0.0.0:80 --timeout 90 --access-logfile - --error-logfile - --log-level info app:app"]
```

---

### Neue Datei: `scripts/prod/validate-prod-environment.sh`

*(Vollständiger Inhalt oben in Lösung 2.1)*

---

### Datei: `scripts/test/test-and-approve-for-prod.sh`

**Performance-Check hinzufügen:**

```bash
# Nach pytest Tests (Zeile ~XX):
echo "🏃 Running performance tests..."
pytest -v -s -m performance tests/test_performance_imports.py

if [ $? -ne 0 ]; then
    echo "❌ Performance tests failed! Not approved for PROD."
    exit 1
fi

# Approval schreiben mit Performance-Flag
echo "$COMMIT_HASH|$TIMESTAMP|SUCCESS|$COMMIT_MSG|true" >> .test-approvals
```

---

## 📊 RISK MATRIX

| Risk | Current | After Fix | Mitigation |
|------|---------|-----------|------------|
| Wrong version on PROD | 🔴 HIGH | 🟢 LOW | Tag-only deployment |
| Wrong database | 🔴 HIGH | 🟢 LOW | Pre-deploy validation |
| Untested code on PROD | 🟡 MED | 🟢 LOW | Test approval required |
| Failed rollback | 🟡 MED | 🟢 LOW | Version-tagged images |
| Performance regression | 🟡 MED | 🟢 LOW | Performance tests in approval |

---

## 🚀 NEXT STEPS

**Immediate Actions:**

1. ✅ Review dieses Dokument
2. ❌ Änderungen NICHT umsetzen (wie gewünscht - nur Analyse)
3. ✅ Entscheidung: Wann soll umgesetzt werden?

**When implementing:**

1. Create `validate-prod-environment.sh`
2. Update `deploy.sh` (remove latest, add DB check)
3. Update `Containerfile` (add validation)
4. Update `test-and-approve-for-prod.sh` (add performance check)
5. Tag current HEAD: `rezept_version_11_11_2025_001`
6. Deploy to PROD with new secure script
7. Verify APP_VERSION != "latest"
8. Test rollback

---

**Erstellt:** 2025-11-11
**Autor:** Claude Code
**Status:** ⚠️ Analysis Only - No changes made yet
