# Deployment Guide - Rezept-Tagebuch

Detaillierte Anleitung für Build, Deployment und Rollback.

**Version:** v25.11.10
**Stand:** November 2025 (Git-Tag-basiertes Deployment seit v25.11.05, vereinfachte Container-Config seit v25.11.10)

---

## 🎯 Deployment-Strategie

### Übersicht

```
Development → Test in Dev → Deploy to Prod → (Rollback if needed)
```

- **DEV**: Entwicklung und Testing mit eigener Datenbank
- **PROD**: Produktiv-System mit Prod-Datenbank
- **Versionierung**: Git-Tag-basiert (z.B. `rezept_version_06_11_2025_001`)
- **Rollback**: Zurück zu jeder getaggten Git-Version
- **Branch**: Nur `main` Branch (keine separate `production` Branch)

### Git-Tag-basierter Workflow

**Alle Deployments erfolgen ausschließlich über Git-Tags!**

```
main Branch → Git-Tag erstellen → Prod Deployment
```

**Wichtig:**
- Es gibt **keinen** separaten `production` Branch
- Alle Git-Tags werden auf `main` erstellt
- Nur getaggte Commits können auf Prod deployed werden
- Working Directory muss clean sein vor Deployment

**Workflow:**
1. Entwickle und teste auf `main` Branch
2. Teste in Dev-Environment (`./scripts/deployment/build-dev.sh`)
3. Committe alle Änderungen
4. Erstelle Git-Tag (`./scripts/tools/tag-version.sh`)
5. Deploy auf Prod (`./scripts/deployment/deploy-prod.sh <GIT_TAG>`)

---

## 📦 Container & Images

### Image-Tags

| Tag                         | Verwendung                          | Beispiel                         |
|-----------------------------|-------------------------------------|----------------------------------|
| `:dev`                      | Development-Container               | `:dev`                           |
| `:rezept_version_DD_MM_YYYY_NNN` | Versionierte Releases         | `:rezept_version_06_11_2025_001` |
| `:latest`                   | Aktuell laufende Prod-Version       | `:latest`                        |

### Container-Übersicht

| Container Name                 | Image Tag  | Network | Database | PostgreSQL Container | Lifecycle |
|--------------------------------|------------|---------|----------|----------------------|-----------|
| `seaser-rezept-tagebuch`       | `:latest`  | seaser-network | `rezepte` (PROD) | `seaser-postgres` | Permanent (systemd) |
| `seaser-rezept-tagebuch-dev`   | `:dev`     | seaser-network | `rezepte_dev` (DEV) | `seaser-postgres-dev` | Permanent (manuell) |
| `seaser-rezept-tagebuch-test`  | `:test`    | seaser-network | `rezepte_test` (TEST) | `seaser-postgres-test` | **On-Demand** (pytest) |

**PostgreSQL Container** (alle permanent):

| Container Name           | Database | Password | Network |
|--------------------------|----------|----------|---------|
| `seaser-postgres`        | `rezepte` | `seaser` | seaser-network |
| `seaser-postgres-dev`    | `rezepte_dev` | `seaser` | seaser-network |
| `seaser-postgres-test`   | `rezepte_test` | `test` | seaser-network |

**Test-Container Lifecycle**: Der Test-Container (`seaser-rezept-tagebuch-test`) startet automatisch wenn `pytest` läuft und stoppt danach wieder. Dies spart Ressourcen, da er nur während Tests benötigt wird. Siehe **tests/README.md** für Details.

---

## 🚀 Deployment-Workflows

### Container-Konfiguration (vereinfacht seit v25.11.10)

**Automatische Umgebungs-Erkennung:**
- `config.py` erkennt die Umgebung anhand von Environment Variables
- DB-Connection-Details werden automatisch gesetzt
- Nur minimale Environment Variables nötig

**Container Start-Commands:**

```bash
# PROD (keine Environment Variables)
podman run -d \
  --name seaser-rezept-tagebuch \
  --network seaser-network \
  -v "$PROJECT_ROOT/data/prod/uploads:/data/uploads:Z" \
  seaser-rezept-tagebuch:latest

# DEV (nur DEV_MODE)
podman run -d \
  --name seaser-rezept-tagebuch-dev \
  --network seaser-network \
  -e DEV_MODE=true \
  -v "$PROJECT_ROOT/data/dev/uploads:/data/dev/uploads:Z" \
  seaser-rezept-tagebuch:dev

# TEST (nur TESTING_MODE)
podman run -d \
  --name seaser-rezept-tagebuch-test \
  --network seaser-network \
  -e TESTING_MODE=true \
  -v "$PROJECT_ROOT/data/test/uploads:/data/test/uploads:Z" \
  seaser-rezept-tagebuch:test
```

**Was config.py automatisch setzt:**
- PROD: `seaser-postgres:5432/rezepte`
- DEV: `seaser-postgres-dev:5432/rezepte_dev`
- TEST: `seaser-postgres-test:5432/rezepte_test`

**Deployment-Scripts verwenden:** Die Scripts `build-dev.sh`, `build-test.sh`, und `deploy-prod.sh` nutzen diese vereinfachte Konfiguration.

---

### Workflow 1: Dev-Entwicklung

**Szenario:** Du möchtest Features entwickeln und testen.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Code ändern
vim app.py
vim index.html

# 2. Dev-Build & Deploy
./scripts/deployment/build-dev.sh

# 3. Testen
# Browser: http://192.168.2.139:8000/rezept-tagebuch-dev/

# 4. Logs prüfen (bei Problemen)
podman logs --tail 50 seaser-rezept-tagebuch-dev
```

**Wichtig:** Dev-Container nutzt `seaser-postgres-dev:rezepte_dev` - komplett getrennt von Prod!

**Automatische Konfiguration seit v25.11.10:**
- `config.py` erkennt automatisch die Umgebung (DEV/TEST/PROD) anhand der Environment Variables
- Nur noch `-e DEV_MODE=true` oder `-e TESTING_MODE=true` nötig
- Keine manuellen DB-Connection-Parameter mehr erforderlich
- Volume Mounts zeigen direkt auf Upload-Verzeichnisse (nicht auf data-Root)

**Details:** Siehe `docs/DATABASE-STORAGE.md` für vollständige Architektur-Dokumentation.

---

### Workflow 2: Production-Deployment

**Szenario:** Features sind in Dev getestet und bereit für Prod.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Git-Tag erstellen (automatisch mit heutigem Datum)
./scripts/tools/tag-version.sh

# 2. Production-Deployment mit Git-Tag
./scripts/deployment/deploy-prod.sh rezept_version_06_11_2025_001
```

**Wichtig:** Nur noch Git-Tag-basiertes Deployment seit v25.11.05! Siehe **GIT-TAG-WORKFLOW.md** für Details.

**Was passiert beim Deployment:**

1. **Prüft Working Directory** (muss clean sein)

2. **Prüft Git-Tag Existenz**

3. **Exportiert Git-Tag** in temp-Directory

4. **Image bauen** aus Git-Tag:
   ```bash
   podman build -t seaser-rezept-tagebuch:rezept_version_06_11_2025_001 ...
   ```

5. **Tag als latest**:
   ```bash
   podman tag seaser-rezept-tagebuch:rezept_version_06_11_2025_001 seaser-rezept-tagebuch:latest
   ```

3. **Alter Container stoppen & entfernen**:
   ```bash
   podman stop seaser-rezept-tagebuch
   podman rm seaser-rezept-tagebuch
   ```

4. **Neuer Container starten** (mit PostgreSQL Prod):
   ```bash
   podman run -d \
     --name seaser-rezept-tagebuch \
     --network seaser-network \
     -v /home/gabor/easer_projekte/rezept-tagebuch/data/prod/uploads:/data/uploads:Z \
     localhost/seaser-rezept-tagebuch:latest
   ```

   **Hinweis:** DB-Connection wird automatisch von `config.py` konfiguriert (keine Environment Variables nötig)

5. **Systemd Service aktualisieren**:
   ```bash
   podman generate systemd --new --name seaser-rezept-tagebuch > \
     /home/gabor/.config/systemd/user/container-seaser-rezept-tagebuch.service
   systemctl --user daemon-reload
   systemctl --user enable container-seaser-rezept-tagebuch.service
   ```

**Deployment verifizieren:**

```bash
# Container läuft?
podman ps | grep seaser-rezept-tagebuch

# Logs OK?
podman logs --tail 20 seaser-rezept-tagebuch

# App erreichbar?
# Browser: http://192.168.2.139:8000/rezept-tagebuch/
```

---

### Workflow 3: Rollback (bei Problemen)

**Szenario:** Neues Deployment hat Fehler, zurück zur vorherigen Version.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Verfügbare Git-Tags prüfen
git tag | grep rezept_version

# Oder verfügbare Images prüfen
podman images | grep seaser-rezept-tagebuch

# Ausgabe:
# localhost/seaser-rezept-tagebuch  rezept_version_06_11_2025_001    abc123...
# localhost/seaser-rezept-tagebuch  rezept_version_05_11_2025_004    def456...
# localhost/seaser-rezept-tagebuch  latest                          abc123...

# 2. Rollback zu alter Version
./scripts/deployment/rollback.sh rezept_version_05_11_2025_004
```

**Was passiert beim Rollback:**

1. **Prüfen ob Git-Tag/Image existiert**
2. **Alte Version als latest taggen**:
   ```bash
   podman tag seaser-rezept-tagebuch:rezept_version_05_11_2025_004 seaser-rezept-tagebuch:latest
   ```
3. **Container neu starten** mit alter Version

**Rollback verifizieren:**

```bash
# Welche Version läuft aktuell?
podman inspect seaser-rezept-tagebuch --format '{{.Image}}'

# Welches Tag hat das Image?
podman images | grep seaser-rezept-tagebuch | grep latest
```

---

## 🔄 Nginx-Proxy Update

**Wann nötig?** Wenn du Nginx-Konfiguration änderst (z.B. neue Routes).

```bash
cd /home/gabor/easer_projekte

# 1. Nginx-Config bearbeiten
vim nginx-proxy-oauth2.conf

# 2. Proxy-Image neu bauen
podman build -t seaser-proxy:latest -f Dockerfile.proxy-oauth2 .

# 3. Proxy neu starten
systemctl --user restart container-seaser-proxy.service

# 4. Nginx-Config testen
podman exec seaser-proxy nginx -t

# 5. Nginx-Logs prüfen
podman logs --tail 50 seaser-proxy
```

---

## 🗄️ Datenbank-Management (PostgreSQL)

### Backup vor Deployment (EMPFOHLEN)

**Prod-Backup vor jedem Deployment:**

```bash
# Automatisches PostgreSQL Backup (wird von deploy-prod.sh gemacht)
podman exec seaser-postgres pg_dump -U postgres rezepte > data/prod/backups/rezepte-backup-before-deploy.sql
```

**Hinweis:** Das Deployment-Script `deploy-prod.sh` erstellt automatisch ein pg_dump Backup vor jedem Deployment.

### Datenbank-Restore (PostgreSQL)

**Falls Deployment schief geht:**

```bash
# PostgreSQL Restore
podman exec -i seaser-postgres psql -U postgres -d rezepte < data/prod/backups/rezepte-backup-TIMESTAMP.sql
```

### Dev-Datenbank zurücksetzen

**Fresh Start für Development:**

```bash
# Dev-Datenbank komplett leeren
podman exec seaser-postgres-dev psql -U postgres -c "DROP DATABASE rezepte_dev;"
podman exec seaser-postgres-dev psql -U postgres -c "CREATE DATABASE rezepte_dev;"

# Schema neu erstellen
podman exec -i seaser-postgres-dev psql -U postgres -d rezepte_dev < scripts/database/schema-postgres.sql

# Dev-Container neu starten
./scripts/deployment/build-dev.sh
```

---

## 📊 Monitoring & Logs

### Container-Status

```bash
# Alle Rezept-Container
podman ps | grep rezept-tagebuch

# Systemd Service Status
systemctl --user status container-seaser-rezept-tagebuch.service
systemctl --user status container-seaser-rezept-tagebuch-dev.service
```

### Logs ansehen

```bash
# Live-Logs (follow)
podman logs -f seaser-rezept-tagebuch

# Letzte 50 Zeilen
podman logs --tail 50 seaser-rezept-tagebuch

# Mit Timestamps
podman logs --tail 50 --timestamps seaser-rezept-tagebuch

# Systemd Journal-Logs
journalctl --user -u container-seaser-rezept-tagebuch.service -f
```

---

## 🐛 Troubleshooting

### Container startet nicht

```bash
# 1. Logs prüfen
podman logs seaser-rezept-tagebuch

# 2. Container manuell starten (debug)
podman run -it --rm \
  --name rezept-debug \
  --network pasta \
  -v /home/gabor/data/rezept-tagebuch:/data:Z \
  localhost/seaser-rezept-tagebuch:latest \
  /bin/bash

# 3. Im Container app.py manuell starten
python app.py
```

### App nicht erreichbar über Nginx

```bash
# 1. Container läuft?
podman ps | grep seaser-rezept-tagebuch

# 2. Nginx-Proxy läuft?
podman ps | grep seaser-proxy

# 3. Nginx-Config testen
podman exec seaser-proxy nginx -t

# 4. Nginx kann Container erreichen?
podman exec seaser-proxy ping seaser-rezept-tagebuch

# 5. DNS-Auflösung im Nginx prüfen
podman exec seaser-proxy nslookup seaser-rezept-tagebuch

# 6. Nginx-Logs prüfen
podman logs seaser-proxy | grep rezept-tagebuch
```

### Falsches Image läuft

```bash
# Welches Image läuft aktuell?
podman inspect seaser-rezept-tagebuch --format '{{.Image}}'

# Alle verfügbaren Images
podman images | grep seaser-rezept-tagebuch

# Container mit spezifischem Image neu starten
podman stop seaser-rezept-tagebuch
podman rm seaser-rezept-tagebuch
podman run -d \
  --name seaser-rezept-tagebuch \
  --network seaser-network \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/prod/uploads:/data/uploads:Z \
  localhost/seaser-rezept-tagebuch:rezept_version_05_11_2025_004
```

---

## 🔐 Security-Hinweise

### Volume-Mounts mit SELinux

**Z-Flag verwenden** für korrekte SELinux-Labels:

```bash
# PROD
-v /home/gabor/easer_projekte/rezept-tagebuch/data/prod/uploads:/data/uploads:Z

# DEV
-v /home/gabor/easer_projekte/rezept-tagebuch/data/dev/uploads:/data/dev/uploads:Z

# TEST
-v /home/gabor/easer_projekte/rezept-tagebuch/data/test/uploads:/data/test/uploads:Z
```

Ohne `:Z` können Permission-Probleme auftreten!

**Wichtig:** Jede Umgebung hat ihr eigenes Upload-Verzeichnis (siehe `docs/DATABASE-STORAGE.md`)

### PostgreSQL Zugriff

```bash
# Prod Database
podman exec -it seaser-postgres psql -U postgres -d rezepte

# Dev Database
podman exec -it seaser-postgres-dev psql -U postgres -d rezepte_dev

# Test Database
podman exec -it seaser-postgres-test psql -U postgres -d rezepte_test
```

---

## 📋 Deployment-Checkliste

### Vor jedem Prod-Deployment:

- [ ] Features in Dev getestet
- [ ] **CHANGELOG.md aktualisiert** mit allen Änderungen seit letztem Release
- [ ] Alle Änderungen committet
- [ ] Prod-Datenbank Backup erstellt
- [ ] Git-Tag erstellt (z.B. rezept_version_06_11_2025_001)
- [ ] Keine laufenden User-Sessions in Prod

### Während Deployment:

- [ ] `./scripts/deployment/deploy-prod.sh <VERSION>` ausführen
- [ ] Container-Start erfolgreich
- [ ] Logs prüfen (keine Errors)
- [ ] App im Browser testen

### Nach Deployment:

- [ ] Alle Features funktionieren
- [ ] Datenbank-Zugriff OK
- [ ] Upload-Funktionen testen
- [ ] Bei Problemen: Rollback durchführen

---

## 📦 Image-Cleanup

**Alte Images entfernen** (Speicherplatz sparen):

```bash
# Alle ungetaggten Images entfernen
podman image prune

# Spezifische alte Version entfernen
podman rmi seaser-rezept-tagebuch:rezept_version_05_10_2025_001

# Alle außer latest + dev + neueste 3 Versionen behalten
# (manuell prüfen und löschen)
podman images | grep seaser-rezept-tagebuch
```

---

## 📝 CHANGELOG Pflege

**Wichtig:** Der CHANGELOG.md muss **vor jedem Deployment** aktualisiert werden!

### Wann CHANGELOG aktualisieren?

**Immer bei:**
- Neuen Features
- Bug-Fixes
- Breaking Changes
- Infrastruktur-Änderungen
- Dokumentations-Updates (wenn relevant)

### Workflow

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Entwicklung & Commits
git add .
git commit -m "feat: Add new feature XYZ"

# 2. CHANGELOG.md bearbeiten
vim CHANGELOG.md

# Füge neuen Eintrag unter [Unreleased] mit heutigem Datum hinzu:
## [Unreleased] - 2025-11-06

### Added
- Neue Feature-Beschreibung

### Fixed
- Bug-Fix-Beschreibung

### Changed
- Änderungs-Beschreibung

# 3. CHANGELOG committen
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v06.11.2025"

# 4. Git-Tag erstellen
./scripts/tools/tag-version.sh

# 5. Deployen
./scripts/deployment/deploy-prod.sh rezept_version_06_11_2025_001
```

### Format-Richtlinien

**Kategorien:**
- `### Added` - Neue Features
- `### Changed` - Änderungen an bestehenden Features
- `### Fixed` - Bug-Fixes
- `### Removed` - Entfernte Features
- `### Security` - Security-relevante Änderungen
- `### Documentation` - Wichtige Doku-Updates

**Best Practices:**
- Nutzer-orientierte Sprache (nicht technische Details)
- Konkrete Beispiele bei wichtigen Changes
- Referenzen zu Issues (z.B. "Issue #9")
- Gruppierung verwandter Changes

**Beispiel:**

```markdown
## [Unreleased] - 2025-11-06

### Fixed - Infrastructure & Project Organization

#### Database & Artifact Consolidation (Issue #9)
- Alle Datenbanken und Runtime-Daten in Projektverzeichnis verschoben
- Neue Struktur: `./data/prod/` und `./data/dev/` im Projekt-Root
- Volume Mounts in Scripts aktualisiert
```

---

## 🔄 Automatisierung (Optional)

### Cronjob für Auto-Backup

```bash
# Crontab bearbeiten
crontab -e

# Täglich um 2 Uhr Prod-Backup
0 2 * * * cp /home/gabor/data/rezept-tagebuch/rezepte.db /home/gabor/data/rezept-tagebuch/rezepte.db.backup-$(date +\%Y\%m\%d)
```

### Git-Integration für Code-Versionierung

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Vor jedem Deployment
git add .
git commit -m "feat: Add new feature XYZ"

# Git-Tag erstellen (automatisch)
./scripts/tools/tag-version.sh

# Deployen mit Git-Tag
./scripts/deployment/deploy-prod.sh rezept_version_06_11_2025_001
```

---

**Erstellt mit ❤️ und Podman**
