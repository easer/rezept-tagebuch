# DEV Services - Rezept-Tagebuch

**Umgebung:** Development
**URL:** http://192.168.2.139:8000/rezept-tagebuch-dev/
**Datenbank:** `seaser-postgres-dev` → DB `rezepte_dev`

---

## 📦 Services in diesem Verzeichnis

### Container Services

#### 1. container-seaser-postgres-dev.service
**Startet:** PostgreSQL DEV Datenbank Container
**Container:** `seaser-postgres-dev`
**Datenbank:** `rezepte_dev`
**Volume:** `/home/gabor/easer_projekte/rezept-tagebuch/data/postgres-dev/`

#### 2. container-seaser-rezept-tagebuch-dev.service
**Startet:** Rezept-Tagebuch DEV App Container
**Container:** `seaser-rezept-tagebuch-dev`
**Image:** `localhost/seaser-rezept-tagebuch:dev`
**Dependencies:** Requires PostgreSQL-dev service
**Volume:** `/home/gabor/easer_projekte/rezept-tagebuch/data/dev/`
**Environment:** `DEV_MODE=true`, `POSTGRES_HOST=seaser-postgres-dev`

---

## 🚀 Installation

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Services kopieren
cp systemd/dev/*.service ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Services aktivieren (Auto-Start)
systemctl --user enable container-seaser-postgres-dev.service
systemctl --user enable container-seaser-rezept-tagebuch-dev.service

# Services starten
systemctl --user start container-seaser-postgres-dev.service
systemctl --user start container-seaser-rezept-tagebuch-dev.service
```

---

## 🔄 Alternative: Manuelle Steuerung

DEV Container können auch manuell über Scripts gesteuert werden:

---

## Container Management

DEV Container wird manuell über Scripts gesteuert:

```bash
# Container neu bauen und starten
./scripts/dev/build.sh

# Container stoppen
podman stop seaser-rezept-tagebuch-dev

# Container starten
podman start seaser-rezept-tagebuch-dev

# Logs ansehen
podman logs -f seaser-rezept-tagebuch-dev
```

---

## Zukünftige Services

Falls du automatische DEV Services brauchst (z.B. regelmäßige Test-Imports), kannst du hier entsprechende .service und .timer Dateien ablegen.

**Beispiel:** DEV Daily Import Service

```ini
[Unit]
Description=Rezept Tagebuch DEV Daily Import
After=network.target seaser-rezept-tagebuch-dev.service

[Service]
Type=oneshot
EnvironmentFile=-/home/gabor/easer_projekte/rezept-tagebuch/.env
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/prod/automation/daily-import-themealdb.sh by_category Dessert
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

**Target:** DEV Container (seaser-rezept-tagebuch-dev)
