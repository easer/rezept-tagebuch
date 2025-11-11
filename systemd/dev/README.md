# DEV Systemd Services

**Target:** DEV Container (seaser-rezept-tagebuch-dev)
**Port:** 8000
**URL:** http://192.168.2.139:8000/rezept-tagebuch-dev/

---

## Status

Aktuell keine DEV-spezifischen systemd Services.

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
