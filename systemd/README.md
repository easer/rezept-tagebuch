# Systemd Services - Rezept-Tagebuch

**Location:** User-Services (`~/.config/systemd/user/`)
**Type:** Systemd Container & Timer Services
**Source of Truth:** Dieses Verzeichnis (versioniert in Git)

---

## 🎯 Struktur

Services sind nach Umgebungen organisiert:

```
systemd/
├── README.md           # Diese Datei
├── prod/               # PROD Services (PostgreSQL + App + Timer)
│   ├── container-seaser-postgres.service
│   ├── container-seaser-rezept-tagebuch.service
│   ├── rezept-daily-import.service
│   ├── rezept-daily-import.timer
│   ├── rezept-daily-migusto-import.service
│   └── rezept-daily-migusto-import.timer
├── dev/                # DEV Services (PostgreSQL + App)
│   ├── container-seaser-postgres-dev.service
│   └── container-seaser-rezept-tagebuch-dev.service
└── test/               # TEST Services (PostgreSQL)
    └── container-seaser-postgres-test.service
```

---

## 📁 PROD Services (systemd/prod/)

### Container Services
- **container-seaser-postgres.service** - PostgreSQL PROD Datenbank
- **container-seaser-rezept-tagebuch.service** - Rezept-Tagebuch PROD App

### Daily Import Timer
- **rezept-daily-import.service + .timer** - TheMealDB Import (06:00 Uhr)
- **rezept-daily-migusto-import.service + .timer** - Migusto.ch Import (07:00 Uhr)

**Details:** Siehe [prod/README.md](prod/README.md)

---

## 📁 DEV Services (systemd/dev/)

### Container Services
- **container-seaser-postgres-dev.service** - PostgreSQL DEV Datenbank
- **container-seaser-rezept-tagebuch-dev.service** - Rezept-Tagebuch DEV App

**Hinweis:** DEV Container können auch manuell über `scripts/deployment/build-dev.sh` gesteuert werden.

**Details:** Siehe [dev/README.md](dev/README.md)

---

## 📁 TEST Services (systemd/test/)

### Container Services
- **container-seaser-postgres-test.service** - PostgreSQL TEST Datenbank

**Hinweis:** TEST App-Container wird on-demand für Tests gestartet (`scripts/testing/run-tests.sh`).

**Details:** Siehe [test/README.md](test/README.md)

---

## 🚀 Installation

### 1. Alle PROD Services installieren

```bash
# Von Projekt-Root aus:
cd /home/gabor/easer_projekte/rezept-tagebuch

# Services kopieren
cp systemd/prod/*.service ~/.config/systemd/user/
cp systemd/prod/*.timer ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Services aktivieren (Auto-Start nach Reboot)
systemctl --user enable container-seaser-postgres.service
systemctl --user enable container-seaser-rezept-tagebuch.service
systemctl --user enable rezept-daily-import.timer
systemctl --user enable rezept-daily-migusto-import.timer

# Services starten (optional, wenn Container noch nicht laufen)
systemctl --user start container-seaser-postgres.service
systemctl --user start container-seaser-rezept-tagebuch.service
systemctl --user start rezept-daily-import.timer
systemctl --user start rezept-daily-migusto-import.timer
```

### 2. DEV Services installieren

```bash
# Services kopieren
cp systemd/dev/*.service ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Services aktivieren
systemctl --user enable container-seaser-postgres-dev.service
systemctl --user enable container-seaser-rezept-tagebuch-dev.service

# Services starten (optional)
systemctl --user start container-seaser-postgres-dev.service
systemctl --user start container-seaser-rezept-tagebuch-dev.service
```

### 3. TEST Services installieren

```bash
# Services kopieren
cp systemd/test/*.service ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Services aktivieren
systemctl --user enable container-seaser-postgres-test.service

# Service starten (optional)
systemctl --user start container-seaser-postgres-test.service
```

---

## 🔄 Services aktualisieren

Nach Änderungen an Service-Dateien:

```bash
# 1. Services im Projekt bearbeiten
vim systemd/prod/container-seaser-rezept-tagebuch.service

# 2. Zu ~/.config/systemd/user/ kopieren
cp systemd/prod/*.service ~/.config/systemd/user/

# 3. Systemd neu laden
systemctl --user daemon-reload

# 4. Service neu starten
systemctl --user restart container-seaser-rezept-tagebuch.service
```

---

## 🔍 Monitoring

### Status prüfen

```bash
# Alle Container-Services
systemctl --user status container-seaser-postgres.service
systemctl --user status container-seaser-rezept-tagebuch.service

# Timer-Status
systemctl --user list-timers

# Alle enabled Services anzeigen
systemctl --user list-unit-files | grep enabled | grep -E "(postgres|rezept)"
```

### Logs ansehen

```bash
# Service-Logs
journalctl --user -u container-seaser-rezept-tagebuch.service

# Import-Logs
journalctl --user -u rezept-daily-import.service --since today

# Live-Logs
journalctl --user -u container-seaser-postgres.service -f
```

### Dependencies prüfen

```bash
# Zeigt alle Dependencies
systemctl --user list-dependencies container-seaser-rezept-tagebuch.service

# Zeigt Requires und After
systemctl --user show container-seaser-rezept-tagebuch.service -p Requires,After
```

---

## 📝 Best Practices

### 1. Lingering aktivieren

User-Services laufen auch ohne Login:

```bash
sudo loginctl enable-linger gabor
```

**Status prüfen:**
```bash
loginctl show-user gabor | grep Linger
# Output: Linger=yes
```

### 2. Services versionieren

Services sind in Git versioniert. Bei Änderungen:

```bash
# Services ändern
vim systemd/prod/container-seaser-rezept-tagebuch.service

# Committen
git add systemd/
git commit -m "Update: Container-Service mit neuen Environment Variables"

# Bei Git-Tag-Deployment werden Services mit deployed
```

### 3. Konsistente Namensgebung

- **Container-Services:** `container-<name>.service`
- **Timer-Services:** `rezept-<feature>.service` + `.timer`
- **Umgebungs-Präfix:** `seaser-postgres`, `seaser-postgres-dev`, `seaser-postgres-test`

### 4. Dependencies beachten

App-Services müssen IMMER nach PostgreSQL starten:

```ini
[Unit]
After=container-seaser-postgres.service
Requires=container-seaser-postgres.service
```

---

## 🐛 Troubleshooting

### Problem: Service lädt alte Version

```bash
# Nach Service-Änderung immer daemon-reload
systemctl --user daemon-reload
systemctl --user restart container-seaser-rezept-tagebuch.service
```

### Problem: Container startet nicht automatisch

```bash
# Service enabled?
systemctl --user is-enabled container-seaser-postgres.service

# Wenn disabled:
systemctl --user enable container-seaser-postgres.service

# Lingering aktiviert?
loginctl show-user gabor | grep Linger
```

### Problem: Dependencies fehlen

```bash
# Dependencies prüfen
systemctl --user show container-seaser-rezept-tagebuch.service -p Requires

# Sollte enthalten: container-seaser-postgres.service
```

### Problem: Service schlägt fehl

```bash
# Logs prüfen
journalctl --user -u container-seaser-rezept-tagebuch.service -n 50

# Container-Status prüfen
podman ps -a | grep rezept-tagebuch
```

---

## 🔗 Weiterführende Dokumentation

- **[prod/README.md](prod/README.md)** - PROD Services Details
- **[dev/README.md](dev/README.md)** - DEV Services Details
- **[test/README.md](test/README.md)** - TEST Services Details
- **[PROD-STABILITY-ANALYSIS.md](../docs/PROD-STABILITY-ANALYSIS.md)** - Systemd Fixes vom 2025-11-11
- **[DEPLOYMENT.md](../docs/DEPLOYMENT.md)** - Deployment-Workflows

---

## ✅ Checkliste: Services nach Server-Reboot

Nach einem Server-Neustart sollten folgende Services automatisch starten:

**PROD:**
- [ ] `container-seaser-postgres.service`
- [ ] `container-seaser-rezept-tagebuch.service`
- [ ] `rezept-daily-import.timer`
- [ ] `rezept-daily-migusto-import.timer`

**DEV:**
- [ ] `container-seaser-postgres-dev.service`
- [ ] `container-seaser-rezept-tagebuch-dev.service`

**TEST:**
- [ ] `container-seaser-postgres-test.service`

**Prüfen:**
```bash
systemctl --user list-units 'container-seaser-*' --all
podman ps | grep -E "(postgres|rezept)"
```

---

**Erstellt:** 2025-11-07
**Aktualisiert:** 2025-11-11 (Container-Services hinzugefügt, komplette Reorganisation)
**Maintainer:** Rezept-Tagebuch DevOps
