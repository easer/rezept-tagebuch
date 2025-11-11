# PROD Stability Analysis & Solutions

**Erstellt:** 2025-11-10
**Problem:** PROD Container fällt wiederholt aus im Podman-Network

---

## 🔍 Root-Cause-Analyse

### Identifizierte Probleme

#### 1. **PostgreSQL Container stoppen automatisch** ⚠️ KRITISCH

**Symptom:**
- PROD/DEV Container laufen, aber API gibt 500 Errors
- Datenbank-Verbindung schlägt fehl
- PostgreSQL Container sind "Exited"

**Root Cause:**
```bash
$ podman ps -a | grep postgres
seaser-postgres          Exited (0) 17 minutes ago
seaser-postgres-dev      Exited (0) 17 minutes ago
seaser-postgres-test     Exited (0) 17 minutes ago
```

Die PostgreSQL Container haben **keine systemd Services** und starten nach System-Reboot oder Absturz nicht automatisch neu.

**Auswirkung:**
- App-Container laufen, können aber keine Daten aus DB laden
- API gibt 500 Internal Server Error
- User kann sich nicht einloggen
- Keine Rezepte sichtbar

**Lösung:**
- Systemd services für alle 3 PostgreSQL Container erstellen
- Auto-Start nach System-Reboot aktivieren
- Dependency-Management: App-Container warten auf PostgreSQL

#### 2. **DEV Container zeigt auf PROD Datenbank** ⚠️ KRITISCH

**Symptom:**
- DEV zeigt gleiche Daten wie PROD
- Keine DEV-spezifischen Bilder
- Gefahr von Daten-Corruption in PROD durch DEV-Testing

**Root Cause:**
```bash
# DEV Container hatte falsche Environment Variables:
POSTGRES_HOST=seaser-postgres  # ❌ FALSCH - zeigt auf PROD!
# FEHLTE: DEV_MODE=true
```

**Korrekte Konfiguration:**
```bash
# PROD Container:
POSTGRES_HOST=seaser-postgres
DB_TYPE=postgresql
APP_VERSION=latest  # oder v25.11.10

# DEV Container:
POSTGRES_HOST=seaser-postgres-dev  # ✅ RICHTIG
DEV_MODE=true
DB_TYPE=postgresql
APP_VERSION=dev
```

**Lösung:**
DEV Container mit korrekten Environment Variables neu starten:
```bash
podman run -d \
    --name seaser-rezept-tagebuch-dev \
    --network seaser-network \
    --env APP_VERSION=dev \
    --env DB_TYPE=postgresql \
    --env DEV_MODE=true \
    --env POSTGRES_HOST=seaser-postgres-dev \
    --env POSTGRES_PASSWORD=seaser \
    --env-file .env \
    --volume seaser-rezept-tagebuch-dev-volume:/data:Z \
    localhost/seaser-rezept-tagebuch:dev
```

#### 3. **PROD läuft mit `:latest` Tag statt versioniertem Tag** ⚠️ MEDIUM

**Symptom:**
- PROD Container hat Image Tag `:latest`
- Kein Git-basiertes Versioning
- Rollback nicht möglich

**Root Cause:**
Container wurde mit `localhost/seaser-rezept-tagebuch:latest` gestartet statt mit spezifischem Git-Tag wie `:rezept_version_10_11_2025_001`.

**Deployment-Standard (laut docs/DEPLOYMENT.md):**
```bash
# ❌ FALSCH:
podman run ... localhost/seaser-rezept-tagebuch:latest

# ✅ RICHTIG:
podman run ... localhost/seaser-rezept-tagebuch:rezept_version_10_11_2025_001
```

**Lösung:**
- Verwende `./scripts/deployment/deploy-prod.sh <GIT_TAG>` für alle PROD Deployments
- `:latest` Tag sollte nur als Symlink auf aktuelles versioned Image zeigen

#### 4. **Config-Drift zwischen .env und Container** ⚠️ LOW

**Symptom:**
- .env Datei hatte `DB_TYPE=postgresql`
- Während Troubleshooting zeitweise auf `sqlite` geändert
- Container lädt alte .env beim Start

**Root Cause:**
Environment wird beim `podman run` geladen, nicht dynamisch aus Datei.

**Lösung:**
- Container muss **neu gestartet** werden nach .env Änderungen
- Klare Trennung: `.env` für shared config, `--env` für environment-spezifische Variablen

---

## ✅ Implementierte Fixes

### 1. PostgreSQL Container gestartet
```bash
podman start seaser-postgres seaser-postgres-dev seaser-postgres-test
```

### 2. DEV Container mit korrekter Config neu gestartet
```bash
podman rm -f seaser-rezept-tagebuch-dev
podman run -d \
    --name seaser-rezept-tagebuch-dev \
    --network seaser-network \
    --env APP_VERSION=dev \
    --env DB_TYPE=postgresql \
    --env DEV_MODE=true \
    --env POSTGRES_HOST=seaser-postgres-dev \
    --env POSTGRES_PASSWORD=seaser \
    --env-file .env \
    --volume seaser-rezept-tagebuch-dev-volume:/data:Z \
    localhost/seaser-rezept-tagebuch:dev
```

### 3. PROD Container neu gestartet
```bash
podman restart seaser-rezept-tagebuch
```

### 4. .env auf PostgreSQL zurückgesetzt
```bash
# .env
DB_TYPE=postgresql
POSTGRES_HOST=seaser-postgres
POSTGRES_PASSWORD=seaser
```

---

## 🔧 Noch zu implementieren

### 1. **Systemd Services für PostgreSQL** ⚠️ KRITISCH

**Status:** TODO
**Priorität:** HOCH

**Aufgabe:**
Erstelle systemd user services für alle 3 PostgreSQL Container:

```bash
# Service erstellen
podman generate systemd --new --name seaser-postgres > \
    ~/.config/systemd/user/container-seaser-postgres.service

podman generate systemd --new --name seaser-postgres-dev > \
    ~/.config/systemd/user/container-seaser-postgres-dev.service

podman generate systemd --new --name seaser-postgres-test > \
    ~/.config/systemd/user/container-seaser-postgres-test.service

# Services aktivieren
systemctl --user daemon-reload
systemctl --user enable container-seaser-postgres.service
systemctl --user enable container-seaser-postgres-dev.service
systemctl --user enable container-seaser-postgres-test.service

# Services starten
systemctl --user start container-seaser-postgres.service
systemctl --user start container-seaser-postgres-dev.service
systemctl --user start container-seaser-postgres-test.service
```

**Dependencies:**
App-Container sollten NACH PostgreSQL starten. In App-Service hinzufügen:
```ini
[Unit]
After=container-seaser-postgres.service
Requires=container-seaser-postgres.service
```

### 2. **Git-Tag-basiertes PROD Deployment** ⚠️ MEDIUM

**Status:** TODO
**Priorität:** MEDIUM

**Aufgabe:**
- Erstelle Git-Tag für aktuelle Version: `v25.11.10`
- Deploy PROD mit versioned Image
- Dokumentiere aktuellen PROD Stand

```bash
# Tag erstellen
./scripts/tools/tag-version.sh  # Erzeugt rezept_version_10_11_2025_001

# Deploy mit Tag
./scripts/deployment/deploy-prod.sh rezept_version_10_11_2025_001
```

### 3. **Health-Check Script** ⚠️ LOW

**Status:** TODO
**Priorität:** LOW

**Aufgabe:**
Erstelle Monitoring-Script das regelmäßig prüft:
- PostgreSQL Container laufen
- App-Container laufen
- API erreichbar (HTTP 200)
- Database-Connection funktioniert

```bash
#!/bin/bash
# /home/gabor/easer_projekte/rezept-tagebuch/scripts/tools/health-check.sh

echo "=== Rezept-Tagebuch Health Check ==="

# PostgreSQL Containers
for db in seaser-postgres seaser-postgres-dev seaser-postgres-test; do
    if podman ps | grep -q $db; then
        echo "✓ $db running"
    else
        echo "✗ $db NOT RUNNING"
    fi
done

# App Containers
for app in seaser-rezept-tagebuch seaser-rezept-tagebuch-dev; do
    if podman ps | grep -q $app; then
        echo "✓ $app running"
    else
        echo "✗ $app NOT RUNNING"
    fi
done

# API Health
curl -s http://10.89.0.190/rezept-tagebuch/api/version && echo "✓ PROD API OK" || echo "✗ PROD API FAILED"
curl -s http://10.89.0.190/rezept-tagebuch-dev/api/version && echo "✓ DEV API OK" || echo "✗ DEV API FAILED"
```

---

## 📊 Aktueller Status

### Container-Status (2025-11-10 22:40 UTC)

| Container | Image | Status | Database | Issue |
|-----------|-------|--------|----------|-------|
| `seaser-postgres` | postgres:16-alpine | ✅ Running | rezepte (4 recipes, 3 users) | ✅ OK |
| `seaser-postgres-dev` | postgres:16-alpine | ✅ Running | rezepte_dev | ✅ OK |
| `seaser-postgres-test` | postgres:16-alpine | ✅ Running | rezepte_test | ✅ OK |
| `seaser-rezept-tagebuch` | `:latest` | ✅ Running | Connects to PROD DB | ⚠️ Needs versioned tag |
| `seaser-rezept-tagebuch-dev` | `:dev` | ✅ Running | Connects to DEV DB | ✅ OK (fixed) |

### API Status

**PROD:**
- ✅ `/api/version` - OK (200)
- ✅ `/api/recipes` - OK (200, 5514 bytes, 4 recipes)
- ✅ `/api/users` - OK (200, 3 users)
- ✅ `/api/uploads/*` - OK (images loading)
- ✅ User Login - Working (user_id=2)

**DEV:**
- 🔄 Testing pending (Container just restarted with correct config)

---

## 🎯 Lessons Learned

### 1. Container-Dependencies sind kritisch
PostgreSQL muss IMMER laufen bevor App-Container starten. Ohne systemd services kann das nicht garantiert werden.

### 2. Environment Variables müssen explizit sein
`DEV_MODE=true` und `POSTGRES_HOST=seaser-postgres-dev` sind essentiell für DEV. Ohne diese Variablen zeigt DEV auf PROD DB.

### 3. Versioned Deployments sind Pflicht
`:latest` Tag ist nicht production-ready. Jedes PROD Deployment braucht Git-Tag für Rollback-Fähigkeit.

### 4. Monitoring & Health-Checks fehlen
Es gibt keinen automatischen Alert wenn PostgreSQL Container stoppen. Health-Check-Script würde früh warnen.

---

## 📋 Action Items

- [ ] **KRITISCH:** Systemd services für PostgreSQL Container erstellen
- [ ] **KRITISCH:** PROD mit versioned Git-Tag neu deployen
- [ ] **MEDIUM:** Health-Check Script implementieren
- [ ] **MEDIUM:** docs/DEPLOYMENT.md um "Troubleshooting" Section erweitern
- [ ] **LOW:** Async Job Endpoints testen (original task)

---

**Status:** PROD läuft stabil (Stand 2025-11-10 22:40 UTC)
**Next Steps:** Systemd services implementieren für langfristige Stabilität
