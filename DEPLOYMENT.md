# Deployment Guide - Rezept-Tagebuch

Detaillierte Anleitung für Build, Deployment und Rollback.

**Version:** v25.11.04
**Stand:** November 2025

---

## 🎯 Deployment-Strategie

### Übersicht

```
Development → Test in Dev → Deploy to Prod → (Rollback if needed)
```

- **DEV**: Entwicklung und Testing mit eigener Datenbank
- **PROD**: Produktiv-System mit Prod-Datenbank
- **Versionierung**: Datum-basierte Tags (z.B. v25.11.04)
- **Rollback**: Zurück zu jeder getaggten Version

### Git Branch-Strategie

Das Projekt verwendet zwei Haupt-Branches:

| Branch       | Zweck                                    | Deploy-Ziel |
|--------------|------------------------------------------|-------------|
| `main`       | Aktive Entwicklung, neue Features       | DEV         |
| `production` | Stabile, getestete Releases              | PROD        |

**Workflow:**
1. Entwickle auf `main` Branch
2. Teste in Dev-Environment (`./build-dev.sh`)
3. Merge `main` → `production` für Prod-Deployment
4. Deploy Production (`./deploy-prod.sh`)

---

## 📦 Container & Images

### Image-Tags

| Tag          | Verwendung                          | Beispiel      |
|--------------|-------------------------------------|---------------|
| `:dev`       | Development-Container               | `:dev`        |
| `:vYY.MM.DD` | Versionierte Releases               | `:v25.11.04`  |
| `:latest`    | Aktuell laufende Prod-Version       | `:latest`     |

### Container-Übersicht

| Container Name                 | Image Tag  | Network | Volume Mount                                        |
|--------------------------------|------------|---------|-----------------------------------------------------|
| `seaser-rezept-tagebuch-dev`   | `:dev`     | pasta   | `/home/gabor/easer_projekte/rezept-tagebuch-data/` |
| `seaser-rezept-tagebuch`       | `:latest`  | pasta   | `/home/gabor/data/rezept-tagebuch/`                |

---

## 🚀 Deployment-Workflows

### Workflow 1: Dev-Entwicklung

**Szenario:** Du möchtest Features entwickeln und testen.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Code ändern
vim app.py
vim index.html

# 2. Dev-Build & Deploy
./build-dev.sh

# 3. Testen
# Browser: http://192.168.2.139:8000/rezept-tagebuch-dev/

# 4. Logs prüfen (bei Problemen)
podman logs --tail 50 seaser-rezept-tagebuch-dev
```

**Wichtig:** Dev-Container nutzt `/easer_projekte/rezept-tagebuch-data/` - komplett getrennt von Prod!

---

### Workflow 2: Production-Deployment

**Szenario:** Features sind in Dev getestet und bereit für Prod.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Production-Deployment mit Version
./deploy-prod.sh 25.11.05

# Oder mit automatischem Datum-Tag
./deploy-prod.sh
```

**Was passiert beim Deployment:**

1. **Image bauen** mit Version-Tag:
   ```bash
   podman build -t seaser-rezept-tagebuch:v25.11.05 -f Containerfile .
   ```

2. **Tag als latest**:
   ```bash
   podman tag seaser-rezept-tagebuch:v25.11.05 seaser-rezept-tagebuch:latest
   ```

3. **Alter Container stoppen & entfernen**:
   ```bash
   podman stop seaser-rezept-tagebuch
   podman rm seaser-rezept-tagebuch
   ```

4. **Neuer Container starten** (mit Prod-Volume):
   ```bash
   podman run -d \
     --name seaser-rezept-tagebuch \
     --network pasta \
     -v /home/gabor/data/rezept-tagebuch:/data:Z \
     localhost/seaser-rezept-tagebuch:latest
   ```

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

### Workflow 2a: Production Release (mit Branch-Merge)

**Szenario:** Du möchtest stabile Features von `main` nach `production` bringen.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Stelle sicher, dass main aktuell ist
git checkout main
git pull origin main

# 2. Wechsle zu production Branch
git checkout production

# 3. Merge main in production
git merge main

# 4. Push production Branch
git push origin production

# 5. Deploy auf Production
./deploy-prod.sh 25.11.05

# App ist jetzt live: http://192.168.2.139:8000/rezept-tagebuch/
```

**Vorteile:**
- ✅ `production` Branch spiegelt exakt den Prod-Stand
- ✅ Klare Trennung zwischen Dev (`main`) und Prod (`production`)
- ✅ Einfaches Rollback zu vorherigen production-Commits
- ✅ Git-History zeigt deutlich, was in Prod deployed ist

---

### Workflow 3: Rollback

**Szenario:** Neues Deployment hat Fehler, zurück zur vorherigen Version.

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# 1. Verfügbare Versionen prüfen
podman images | grep seaser-rezept-tagebuch

# Ausgabe:
# localhost/seaser-rezept-tagebuch  v25.11.05    abc123...
# localhost/seaser-rezept-tagebuch  v25.11.04    def456...
# localhost/seaser-rezept-tagebuch  latest       abc123...

# 2. Rollback zu alter Version
./rollback.sh v25.11.04
```

**Was passiert beim Rollback:**

1. **Prüfen ob Version existiert**
2. **Alte Version als latest taggen**:
   ```bash
   podman tag seaser-rezept-tagebuch:v25.11.04 seaser-rezept-tagebuch:latest
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

## 🗄️ Datenbank-Management

### Backup vor Deployment (EMPFOHLEN)

**Prod-Backup vor jedem Deployment:**

```bash
# Automatisches Backup mit Datum
cp /home/gabor/data/rezept-tagebuch/rezepte.db \
   /home/gabor/data/rezept-tagebuch/rezepte.db.backup-$(date +%Y%m%d-%H%M%S)
```

**Backup in Deployment-Script integrieren:**

```bash
# In deploy-prod.sh vor Container-Neustart einfügen:
echo "📦 Creating database backup..."
cp /home/gabor/data/rezept-tagebuch/rezepte.db \
   /home/gabor/data/rezept-tagebuch/rezepte.db.backup-$(date +%Y%m%d-%H%M%S)
```

### Datenbank-Restore

**Falls Deployment schief geht:**

```bash
# Container stoppen
podman stop seaser-rezept-tagebuch

# Backup wiederherstellen
cp /home/gabor/data/rezept-tagebuch/rezepte.db.backup-20251104-123000 \
   /home/gabor/data/rezept-tagebuch/rezepte.db

# Container starten
podman start seaser-rezept-tagebuch
```

### Dev-Daten von Prod kopieren (zum Testen)

```bash
# Prod-Datenbank nach Dev kopieren
cp /home/gabor/data/rezept-tagebuch/rezepte.db \
   /home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db

# Dev-Container neu starten
./build-dev.sh
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
  --network pasta \
  -v /home/gabor/data/rezept-tagebuch:/data:Z \
  localhost/seaser-rezept-tagebuch:v25.11.04
```

---

## 🔐 Security-Hinweise

### Volume-Mounts mit SELinux

**Z-Flag verwenden** für korrekte SELinux-Labels:

```bash
-v /home/gabor/data/rezept-tagebuch:/data:Z
```

Ohne `:Z` können Permission-Probleme auftreten!

### Datenbank-Permissions

```bash
# Prüfen
ls -lh /home/gabor/data/rezept-tagebuch/

# Sollte sein:
# -rw-r--r-- gabor gabor rezepte.db
```

---

## 📋 Deployment-Checkliste

### Vor jedem Prod-Deployment:

- [ ] Features in Dev getestet
- [ ] Prod-Datenbank Backup erstellt
- [ ] Version-Tag gewählt (z.B. v25.11.05)
- [ ] Keine laufenden User-Sessions in Prod

### Während Deployment:

- [ ] `./deploy-prod.sh <VERSION>` ausführen
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
podman rmi seaser-rezept-tagebuch:v25.10.01

# Alle außer latest + dev + neueste 3 Versionen behalten
# (manuell prüfen und löschen)
podman images | grep seaser-rezept-tagebuch
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

# Git initialisieren (falls noch nicht)
git init
git add app.py index.html Containerfile requirements.txt
git commit -m "Version v25.11.04"
git tag v25.11.04

# Vor jedem Deployment
git add .
git commit -m "Version v25.11.05 - New feature XYZ"
git tag v25.11.05
./deploy-prod.sh 25.11.05
```

---

**Erstellt mit ❤️ und Podman**
