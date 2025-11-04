# Rezept-Tagebuch App

Eine Flask-basierte Web-App zum Verwalten von Rezepten und Tagebucheinträgen.

**Version:** v25.11.04
**Stand:** November 2025

---

## 🚀 Schnellstart

### Zugriff auf die Apps

**PRODUCTION:**
```
http://192.168.2.139:8000/rezept-tagebuch/
```

**DEVELOPMENT:**
```
http://192.168.2.139:8000/rezept-tagebuch-dev/
```

**Authentifizierung:**
- Kein Passwort im LAN (192.168.2.x) und VPN (Tailscale)
- Passwort erforderlich bei externem Zugriff

---

## 📦 Container-Architektur

### Container-Setup

```
┌─────────────────────────────────────────────┐
│  Nginx Proxy (seaser-proxy)                │
│  Port 8000 (HTTP), 8443/8444 (HTTPS)      │
└─────────────┬──────────────────┬────────────┘
              │                  │
    /rezept-tagebuch/    /rezept-tagebuch-dev/
              │                  │
              ▼                  ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ PROD Container  │  │ DEV Container   │
    │ Port: intern    │  │ Port: intern    │
    └────────┬────────┘  └────────┬────────┘
             │                    │
             ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ Prod Database   │  │ Dev Database    │
    │ /data/rezept-   │  │ /easer_projekte/│
    │ tagebuch/       │  │ rezept-tagebuch-│
    │                 │  │ data/           │
    └─────────────────┘  └─────────────────┘
```

### Volumes (Datenbanken)

| Environment | Volume Mount                                        | Datenbank            |
|-------------|-----------------------------------------------------|----------------------|
| **DEV**     | `/home/gabor/easer_projekte/rezept-tagebuch-data/` | `rezepte.db`         |
| **PROD**    | `/home/gabor/data/rezept-tagebuch/`                 | `rezepte.db`         |

**Wichtig:** Getrennte Datenbanken = sicheres Testen ohne Risiko für Prod-Daten!

### Container-Namen

| Environment | Container Name                 | Image Tag      |
|-------------|--------------------------------|----------------|
| **DEV**     | `seaser-rezept-tagebuch-dev`   | `:dev`         |
| **PROD**    | `seaser-rezept-tagebuch`       | `:latest`      |

---

## 🛠️ Entwicklungs-Workflow

### 1. In Dev entwickeln & testen

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Code ändern (app.py, index.html, etc.)
vim app.py

# Dev-Container neu bauen und starten
./build-dev.sh

# Testen auf: http://192.168.2.139:8000/rezept-tagebuch-dev/
```

### 2. Auf Prod deployen

```bash
# Mit Versions-Tag deployen
./deploy-prod.sh 25.11.05

# Oder mit aktuellem Datum (automatisch)
./deploy-prod.sh

# Prod-App ist nun auf: http://192.168.2.139:8000/rezept-tagebuch/
```

### 3. Rollback bei Problemen

```bash
# Verfügbare Versionen anzeigen
podman images | grep seaser-rezept-tagebuch

# Zurück zu alter Version
./rollback.sh v25.11.04
```

---

## 📝 Scripts

### build-dev.sh

Baut Dev-Image und startet Dev-Container neu.

```bash
./build-dev.sh
```

**Was passiert:**
1. Baut Image `seaser-rezept-tagebuch:dev`
2. Stoppt alten Dev-Container
3. Startet neuen Dev-Container mit Dev-Datenbank

### deploy-prod.sh

Deployed getaggte Version auf Production.

```bash
./deploy-prod.sh [VERSION]

# Beispiele:
./deploy-prod.sh 25.11.05    # Mit spezifischer Version
./deploy-prod.sh              # Mit aktuellem Datum
```

**Was passiert:**
1. Baut Image mit Version-Tag (z.B. `v25.11.05`)
2. Tagged Image als `:latest`
3. Stoppt alten Prod-Container
4. Startet neuen Prod-Container mit Prod-Datenbank
5. Aktualisiert systemd Service

### rollback.sh

Rollback zu vorheriger Version.

```bash
./rollback.sh <VERSION>

# Beispiel:
./rollback.sh v25.11.04
```

**Was passiert:**
1. Prüft ob Version existiert
2. Tagged alte Version als `:latest`
3. Startet Prod-Container mit alter Version neu

---

## 🐳 Container-Management

### Container Status prüfen

```bash
# Beide Container anzeigen
podman ps | grep rezept-tagebuch

# Logs ansehen
podman logs --tail 20 seaser-rezept-tagebuch      # PROD
podman logs --tail 20 seaser-rezept-tagebuch-dev  # DEV
```

### Container manuell starten/stoppen

```bash
# DEV
podman stop seaser-rezept-tagebuch-dev
podman start seaser-rezept-tagebuch-dev

# PROD
podman stop seaser-rezept-tagebuch
podman start seaser-rezept-tagebuch
```

### Systemd Services

```bash
# Status prüfen
systemctl --user status container-seaser-rezept-tagebuch.service      # PROD
systemctl --user status container-seaser-rezept-tagebuch-dev.service  # DEV

# Neu starten
systemctl --user restart container-seaser-rezept-tagebuch.service
systemctl --user restart container-seaser-rezept-tagebuch-dev.service
```

---

## 🗄️ Datenbank-Zugriff

### Dev-Datenbank

```bash
sqlite3 /home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db
```

### Prod-Datenbank

```bash
sqlite3 /home/gabor/data/rezept-tagebuch/rezepte.db
```

### Backup erstellen

```bash
# Dev Backup
cp /home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db \
   /home/gabor/easer_projekte/rezept-tagebuch-data/rezepte.db.backup-$(date +%Y%m%d)

# Prod Backup
cp /home/gabor/data/rezept-tagebuch/rezepte.db \
   /home/gabor/data/rezept-tagebuch/rezepte.db.backup-$(date +%Y%m%d)
```

---

## 📚 Dokumentation

- **README.md** - Dieses Dokument (Übersicht & Workflows)
- **DEPLOYMENT.md** - Detaillierte Deployment-Anleitung
- **UX-GUIDE.md** - Design-Richtlinien und Best Practices

---

## 🔧 Technologie-Stack

- **Backend:** Python Flask
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Datenbank:** SQLite
- **Container:** Podman
- **Proxy:** Nginx
- **Services:** systemd (user services)

---

## 🎨 UX-Richtlinien

Siehe **UX-GUIDE.md** für:
- CSS-Regeln und Best Practices
- CRUD-Pattern
- Design-System
- Entwicklungs-Workflow

---

## 📞 Troubleshooting

### Dev-App lädt nicht

```bash
# Container-Logs prüfen
podman logs seaser-rezept-tagebuch-dev

# Container neu starten
./build-dev.sh
```

### Prod-App lädt nicht

```bash
# Container-Logs prüfen
podman logs seaser-rezept-tagebuch

# Nginx-Proxy neu starten
systemctl --user restart container-seaser-proxy.service

# Container neu starten
systemctl --user restart container-seaser-rezept-tagebuch.service
```

### Nginx-Routing funktioniert nicht

```bash
# Nginx-Config prüfen
podman exec seaser-proxy nginx -t

# Nginx-Logs ansehen
podman logs seaser-proxy --tail 50
```

---

## 📄 Lizenz

Privates Projekt für den Heimgebrauch.

---

**Erstellt mit ❤️ und Podman**
