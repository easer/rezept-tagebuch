# Quadlets - Modern Podman + systemd Integration

**Location:** `~/.config/containers/systemd/`
**Type:** Podman Quadlets (Pods + Containers + Timers)
**Source of Truth:** Dieses Verzeichnis (versioniert in Git)

---

## 🚀 Was sind Quadlets?

Quadlets sind die **moderne Art** Container mit systemd zu verwalten:

- ✅ **60% weniger Code** als klassische `.service` Files
- ✅ **Viel lesbarer** - Keine komplexen `podman run` Befehle
- ✅ **Pods Support** - Logische Gruppierung von Containern
- ✅ **Auto-Generated** - systemd generiert `.service` Files automatisch
- ✅ **Best Practices** - Podman managed alle Details

---

## 📁 Struktur

```
systemd/quadlets/
├── README.md           # Diese Datei
├── prod/               # PROD Pod + Containers + Timers
│   ├── rezept-prod.pod
│   ├── rezept-prod-postgres.container
│   ├── rezept-prod-app.container
│   ├── rezept-daily-import.service + .timer
│   └── rezept-daily-migusto-import.service + .timer
├── dev/                # DEV Pod + Containers
│   ├── rezept-dev.pod
│   ├── rezept-dev-postgres.container
│   └── rezept-dev-app.container
└── test/               # TEST Pod + Container
    ├── rezept-test.pod
    └── rezept-test-postgres.container
```

---

## 🎯 Pod Architecture

### PROD Pod
```
rezept-prod.pod
├── rezept-prod-postgres.container (seaser-postgres)
│   └── Database: rezepte
│   └── Port: 5432 (localhost only)
└── rezept-prod-app.container (seaser-rezept-tagebuch)
    └── POSTGRES_HOST=localhost ← Pod Networking!
    └── URL: http://192.168.2.139:8000/rezept-tagebuch/
```

### DEV Pod
```
rezept-dev.pod
├── rezept-dev-postgres.container (seaser-postgres-dev)
│   └── Database: rezepte_dev
│   └── Port: 5432 (localhost only)
└── rezept-dev-app.container (seaser-rezept-tagebuch-dev)
    └── POSTGRES_HOST=localhost
    └── URL: http://192.168.2.139:8000/rezept-tagebuch-dev/
```

### TEST Pod
```
rezept-test.pod
└── rezept-test-postgres.container (seaser-postgres-test)
    └── Database: rezepte_test
    └── Port: 5432 (localhost only)
    └── App: on-demand via pytest
```

---

## 🚀 Installation

### 1. Quadlets nach ~/.config/containers/systemd/ kopieren

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# PROD installieren
mkdir -p ~/.config/containers/systemd
cp systemd/quadlets/prod/* ~/.config/containers/systemd/

# DEV installieren (optional)
cp systemd/quadlets/dev/* ~/.config/containers/systemd/

# TEST installieren (optional)
cp systemd/quadlets/test/* ~/.config/containers/systemd/

# Systemd neu laden (generiert .service files automatisch!)
systemctl --user daemon-reload
```

### 2. Services enablen

```bash
# PROD Pod
systemctl --user enable rezept-prod.pod
systemctl --user enable rezept-prod-postgres.container
systemctl --user enable rezept-prod-app.container
systemctl --user enable rezept-daily-import.timer
systemctl --user enable rezept-daily-migusto-import.timer

# DEV Pod
systemctl --user enable rezept-dev.pod
systemctl --user enable rezept-dev-postgres.container
systemctl --user enable rezept-dev-app.container

# TEST Pod
systemctl --user enable rezept-test.pod
systemctl --user enable rezept-test-postgres.container
```

### 3. Services starten

```bash
# PROD starten (startet automatisch: pod → postgres → app)
systemctl --user start rezept-prod-app.container

# DEV starten
systemctl --user start rezept-dev-app.container

# TEST starten
systemctl --user start rezept-test-postgres.container

# Timer starten
systemctl --user start rezept-daily-import.timer
systemctl --user start rezept-daily-migusto-import.timer
```

---

## 🔄 Migration von alten Services

### Alte Services stoppen

```bash
# Alte Container-Services stoppen
systemctl --user stop container-seaser-postgres.service
systemctl --user stop container-seaser-postgres-dev.service
systemctl --user stop container-seaser-postgres-test.service
systemctl --user stop container-seaser-rezept-tagebuch.service
systemctl --user stop container-seaser-rezept-tagebuch-dev.service

# Alte Container stoppen (falls noch aktiv)
podman stop seaser-postgres seaser-postgres-dev seaser-postgres-test
podman stop seaser-rezept-tagebuch seaser-rezept-tagebuch-dev
```

### Alte Services deaktivieren

```bash
# Deaktivieren (Auto-Start entfernen)
systemctl --user disable container-seaser-postgres.service
systemctl --user disable container-seaser-postgres-dev.service
systemctl --user disable container-seaser-postgres-test.service
systemctl --user disable container-seaser-rezept-tagebuch.service
systemctl --user disable container-seaser-rezept-tagebuch-dev.service
```

### Alte Service-Files löschen (optional)

```bash
# ACHTUNG: Erst nach erfolgreicher Migration!
rm ~/.config/systemd/user/container-seaser-postgres*.service
rm ~/.config/systemd/user/container-seaser-rezept-tagebuch*.service

systemctl --user daemon-reload
```

---

## 🔍 Monitoring

### Pod Status

```bash
# Alle Pods anzeigen
podman pod ps

# Pod Details
podman pod inspect rezept-prod

# Container in Pod
podman pod ps --format "{{.Name}}: {{.Status}}" rezept-prod

# Pod Stats (CPU, Memory)
podman pod stats rezept-prod
```

### Service Status

```bash
# Generierte Services anzeigen
systemctl --user list-units 'rezept-*'

# Pod Service Status
systemctl --user status rezept-prod.pod

# Container Service Status
systemctl --user status rezept-prod-postgres.container
systemctl --user status rezept-prod-app.container

# Timer Status
systemctl --user list-timers rezept-daily*
```

### Logs

```bash
# Pod Logs (alle Container)
podman pod logs rezept-prod

# Einzelner Container
podman logs seaser-postgres
podman logs seaser-rezept-tagebuch

# Via systemd
journalctl --user -u rezept-prod-app.container -f
```

---

## 🎛️ Management

### Pod Operations

```bash
# Ganzen Pod starten
systemctl --user start rezept-prod.pod

# Ganzen Pod stoppen
systemctl --user stop rezept-prod.pod

# Ganzen Pod neu starten
systemctl --user restart rezept-prod.pod

# Pod pausieren (alle Container)
podman pod pause rezept-prod

# Pod fortsetzen
podman pod unpause rezept-prod
```

### Container Operations

```bash
# Einzelnen Container starten
systemctl --user start rezept-prod-postgres.container

# Einzelnen Container stoppen
systemctl --user stop rezept-prod-app.container

# Container neu starten
systemctl --user restart rezept-prod-app.container
```

### Dependency Order

Systemd startet automatisch in richtiger Reihenfolge:
1. `rezept-prod.pod` (Erstellt Pod)
2. `rezept-prod-postgres.container` (Startet DB)
3. `rezept-prod-app.container` (Startet App, wartet auf DB)

---

## 📝 Quadlets Syntax

### .pod File Format

```ini
[Unit]
Description=My Pod
After=network-online.target

[Pod]
PodName=my-pod-name
Network=my-network

[Install]
WantedBy=default.target
```

### .container File Format

```ini
[Unit]
Description=My Container
Requires=my-pod.pod
After=my-pod.pod

[Container]
Image=docker.io/library/postgres:16
ContainerName=my-container
Pod=my-pod.pod
Environment=KEY=value
Volume=/host/path:/container/path:Z

[Service]
Restart=on-failure

[Install]
WantedBy=default.target
```

---

## 🔧 Troubleshooting

### Problem: Services werden nicht generiert

```bash
# Daemon reload manuell triggern
systemctl --user daemon-reload

# Generierte Services prüfen
ls ~/.config/systemd/user.control/

# Quadlet Generator Logs
journalctl --user -u systemd-generator-podman
```

### Problem: Pod startet nicht

```bash
# Pod Status
podman pod ps -a

# Pod Logs
podman pod logs rezept-prod

# Service Status
systemctl --user status rezept-prod.pod

# Service Logs
journalctl --user -u rezept-prod.pod
```

### Problem: Container verbindet nicht zur DB

```bash
# In Pod? (localhost funktioniert nur IN Pod)
podman pod ps | grep rezept-prod

# Beide Container im gleichen Pod?
podman ps --filter pod=rezept-prod

# DB erreichbar via localhost?
podman exec seaser-rezept-tagebuch ping localhost
podman exec seaser-rezept-tagebuch nc -zv localhost 5432
```

### Problem: Alte Container laufen noch

```bash
# Alte Container finden
podman ps -a | grep -E "(seaser-postgres|seaser-rezept)"

# Alte Container stoppen
podman stop seaser-postgres seaser-postgres-dev
podman stop seaser-rezept-tagebuch seaser-rezept-tagebuch-dev

# Alte Container löschen
podman rm seaser-postgres seaser-postgres-dev
podman rm seaser-rezept-tagebuch seaser-rezept-tagebuch-dev
```

---

## 🆚 Vergleich: Alte Services vs. Quadlets

### Alte .service Datei (44 Zeilen)
```systemd
[Unit]
Description=Podman container-seaser-postgres.service
Wants=network-online.target
After=network-online.target
RequiresMountsFor=%t/containers

[Service]
Environment=PODMAN_SYSTEMD_UNIT=%n
Restart=on-failure
TimeoutStopSec=70
ExecStart=/usr/bin/podman run \
  --cidfile=%t/%n.ctr-id \
  --cgroups=no-conmon \
  --rm \
  --sdnotify=conmon \
  --replace \
  -d \
  --name seaser-postgres \
  --network seaser-network \
  -e POSTGRES_PASSWORD=seaser \
  -e POSTGRES_DB=rezepte \
  -e POSTGRES_USER=postgres \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/postgres:/var/lib/postgresql/data:Z \
  docker.io/library/postgres:16-alpine
ExecStop=/usr/bin/podman stop --ignore -t 10 --cidfile=%t/%n.ctr-id
ExecStopPost=/usr/bin/podman rm -f --ignore -t 10 --cidfile=%t/%n.ctr-id
Type=notify
NotifyAccess=all

[Install]
WantedBy=default.target
```

### Neue .container Quadlet (17 Zeilen)
```ini
[Unit]
Description=PostgreSQL Database for Rezept-Tagebuch PROD
Requires=rezept-prod.pod
After=rezept-prod.pod

[Container]
Image=docker.io/library/postgres:16-alpine
ContainerName=seaser-postgres
Pod=rezept-prod.pod
Environment=POSTGRES_PASSWORD=seaser
Environment=POSTGRES_DB=rezepte
Environment=POSTGRES_USER=postgres
Volume=/home/gabor/easer_projekte/rezept-tagebuch/data/postgres:/var/lib/postgresql/data:Z

[Service]
Restart=on-failure

[Install]
WantedBy=default.target
```

**Ersparnis:** 61% weniger Code, viel lesbarer!

---

## ✅ Vorteile von Pods

1. **Shared Networking** - Container kommunizieren via `localhost`
2. **Logische Gruppierung** - PROD/DEV/TEST klar getrennt
3. **Atomic Operations** - Pod starten = alle Container starten
4. **Einfachere Dependencies** - App wartet automatisch auf DB im Pod
5. **Resource Limits** - Pod-Level CPU/Memory Limits möglich
6. **Besseres Monitoring** - `podman pod stats` zeigt Pod-Stats

---

## 🔗 Weiterführende Dokumentation

- **[Podman Quadlets](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html)** - Offizielle Docs
- **[systemd/README.md](../README.md)** - Alte Service-Dokumentation
- **[PROD-STABILITY-ANALYSIS.md](../../docs/PROD-STABILITY-ANALYSIS.md)** - Stability Fixes

---

**Erstellt:** 2025-11-11
**Migration:** Alte Services → Pods + Quadlets
**Maintainer:** Rezept-Tagebuch DevOps
