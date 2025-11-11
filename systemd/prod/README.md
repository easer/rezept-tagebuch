# PROD Services - Rezept-Tagebuch

**Umgebung:** Production
**URL:** http://192.168.2.139:8000/rezept-tagebuch/
**Datenbank:** `seaser-postgres` → DB `rezepte`

---

## 📦 Services in diesem Verzeichnis

### Container Services

#### 1. container-seaser-postgres.service
**Startet:** PostgreSQL PROD Datenbank Container
**Container:** `seaser-postgres`
**Datenbank:** `rezepte`
**Volume:** `/home/gabor/easer_projekte/rezept-tagebuch/data/postgres/`

#### 2. container-seaser-rezept-tagebuch.service
**Startet:** Rezept-Tagebuch PROD App Container
**Container:** `seaser-rezept-tagebuch`
**Image:** `localhost/seaser-rezept-tagebuch:latest`
**Dependencies:** Requires PostgreSQL service
**Volume:** `/home/gabor/easer_projekte/rezept-tagebuch/data/prod/`

### Timer Services

#### 3. rezept-daily-import (TheMealDB)

**Files:**
- `rezept-daily-import.service`
- `rezept-daily-import.timer`

**Script:** `scripts/prod/automation/daily-import-themealdb.sh`

**Schedule:** Täglich um 06:00 UTC

**Purpose:** Importiert täglich ein vegetarisches Rezept von TheMealDB

**Features:**
- Meat-Filter Protection (lehnt Fleisch-Rezepte ab)
- Automatische Retry-Logik (bis zu 10 Versuche)
- Cleanup alter Auto-Imports

---

### 2. rezept-daily-migusto-import

**Files:**
- `rezept-daily-migusto-import.service`
- `rezept-daily-migusto-import.timer`

**Script:** `scripts/prod/automation/daily-import-migusto.sh`

**Schedule:** Täglich um 07:00 UTC

**Purpose:** Importiert täglich ein zufälliges Rezept von Migusto

---

## Installation

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Services kopieren
cp systemd/prod/rezept-daily-import.service ~/.config/systemd/user/
cp systemd/prod/rezept-daily-import.timer ~/.config/systemd/user/
cp systemd/prod/rezept-daily-migusto-import.service ~/.config/systemd/user/
cp systemd/prod/rezept-daily-migusto-import.timer ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Timer aktivieren und starten
systemctl --user enable rezept-daily-import.timer
systemctl --user start rezept-daily-import.timer
systemctl --user enable rezept-daily-migusto-import.timer
systemctl --user start rezept-daily-migusto-import.timer
```

Oder verwende das install Script:

```bash
./scripts/prod/install-daily-import.sh
```

---

## Monitoring

### Status prüfen

```bash
# Alle Timer anzeigen
systemctl --user list-timers | grep rezept

# Service-Status
systemctl --user status rezept-daily-import.timer
systemctl --user status rezept-daily-migusto-import.timer
```

### Logs ansehen

```bash
# TheMealDB Import Logs
journalctl --user -u rezept-daily-import.service --since today

# Migusto Import Logs
journalctl --user -u rezept-daily-migusto-import.service --since today

# Live Logs
journalctl --user -u rezept-daily-import.service -f
```

### Manuell triggern

```bash
# Service manuell ausführen
systemctl --user start rezept-daily-import.service
systemctl --user start rezept-daily-migusto-import.service

# Logs verfolgen
journalctl --user -u rezept-daily-import.service -f
```

---

## Deinstallation

```bash
# Timer stoppen
systemctl --user stop rezept-daily-import.timer
systemctl --user stop rezept-daily-migusto-import.timer

# Timer deaktivieren
systemctl --user disable rezept-daily-import.timer
systemctl --user disable rezept-daily-migusto-import.timer

# Dateien löschen
rm ~/.config/systemd/user/rezept-daily-import.{service,timer}
rm ~/.config/systemd/user/rezept-daily-migusto-import.{service,timer}

# Systemd neu laden
systemctl --user daemon-reload
```

---

## Troubleshooting

### Problem: Timer läuft nicht nach Server-Neustart

**Lösung:** Lingering aktivieren

```bash
sudo loginctl enable-linger gabor
loginctl show-user gabor | grep Linger
# Sollte zeigen: Linger=yes
```

### Problem: Service failed

```bash
# Logs prüfen
journalctl --user -u rezept-daily-import.service --since today

# Container läuft?
podman ps | grep seaser-rezept-tagebuch

# API erreichbar?
curl http://localhost:8000/rezept-tagebuch/
```

---

**Target:** PROD Container (seaser-rezept-tagebuch)
