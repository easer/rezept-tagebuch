# Systemd Services - Rezept-Tagebuch

**Location:** User-Services (`~/.config/systemd/user/`)
**Type:** Systemd Timer (wie Cron, aber besser)

---

## 🎯 Struktur

Services sind nach Umgebungen organisiert:

```
systemd/
├── prod/        PROD Services (seaser-rezept-tagebuch)
├── dev/         DEV Services (seaser-rezept-tagebuch-dev)
└── test/        TEST Services (seaser-rezept-tagebuch-test)
```

---

## 📁 PROD Services (systemd/prod/)

### Daily Import Services

**Files:**
- `rezept-daily-import.service` + `rezept-daily-import.timer`
- `rezept-daily-migusto-import.service` + `rezept-daily-migusto-import.timer`

**Purpose:** Tägliche automatische Rezept-Imports auf PROD Container

**Details:** Siehe [systemd/prod/README.md](prod/README.md)

---

## 📁 DEV Services (systemd/dev/)

Aktuell keine DEV-spezifischen Services.

DEV Container wird manuell über `scripts/dev/build.sh` gesteuert.

---

## 📁 TEST Services (systemd/test/)

Aktuell keine TEST-spezifischen Services.

TEST Container wird on-demand für Testing gestartet (`scripts/test/test-and-approve-for-prod.sh`).

---

## 🚀 Installation

Services müssen nach `~/.config/systemd/user/` kopiert werden:

```bash
# Beispiel: PROD Daily Import
cp systemd/prod/rezept-daily-import.service ~/.config/systemd/user/
cp systemd/prod/rezept-daily-import.timer ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable rezept-daily-import.timer
systemctl --user start rezept-daily-import.timer
```

**Wichtig:** User-Services (nicht System-Services!)

---

## 🔍 Monitoring

```bash
# Alle Timer anzeigen
systemctl --user list-timers

# Service-Status
systemctl --user status rezept-daily-import.timer

# Logs ansehen
journalctl --user -u rezept-daily-import.service --since today
```

---

## 📝 Best Practices

### Lingering aktivieren

User-Services laufen auch ohne Login:

```bash
sudo loginctl enable-linger gabor
```

### Nach Änderungen neu laden

```bash
systemctl --user daemon-reload
systemctl --user restart <service>.timer
```

---

**Erstellt:** 2025-11-07
**Aktualisiert:** 2025-11-11 (Umgebungs-basierte Organisation)
