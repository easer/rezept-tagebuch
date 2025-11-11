# TEST Services - Rezept-Tagebuch

**Umgebung:** Test
**Datenbank:** `seaser-postgres-test` → DB `rezepte_test`
**Nutzung:** On-demand für pytest Test-Runs

---

## 📦 Services in diesem Verzeichnis

### Container Services

#### 1. container-seaser-postgres-test.service
**Startet:** PostgreSQL TEST Datenbank Container
**Container:** `seaser-postgres-test`
**Datenbank:** `rezepte_test`
**Volume:** `/home/gabor/easer_projekte/rezept-tagebuch/data/postgres-test/`
**Password:** `test` (abweichend von PROD/DEV!)

---

## 🚀 Installation

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Service kopieren
cp systemd/test/*.service ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Service aktivieren (Auto-Start)
systemctl --user enable container-seaser-postgres-test.service

# Service starten
systemctl --user start container-seaser-postgres-test.service
```

---

## 📝 Hinweise

### TEST App-Container

Es gibt **keinen** systemd service für den TEST App-Container (`seaser-rezept-tagebuch-test`).

**Warum?** Der TEST App-Container wird on-demand von pytest gestartet und gestoppt.

---

## Container Management

TEST Container wird on-demand für Testing gestartet:

```bash
# Vollständiger Test-Workflow (baut, startet, testet, stoppt Container)
./scripts/test/test-and-approve-for-prod.sh

# Tests laufen lassen (Container muss bereits laufen)
./scripts/test/run-tests.sh

# Container manuell bauen
./scripts/test/build.sh
```

---

## Test-Strategie

TEST Container ist **on-demand only**:
1. Wird von `test-and-approve-for-prod.sh` gestartet
2. Tests werden ausgeführt
3. Container wird automatisch gestoppt nach Tests
4. Läuft NICHT permanent im Hintergrund

**Warum?** TEST Container wird nur für explizite Test-Runs benötigt, nicht für dauerhafte Services.

---

## Zukünftige Services

Falls du automatische TEST Services brauchst (z.B. nächtliche Test-Runs), kannst du hier entsprechende .service und .timer Dateien ablegen.

**Beispiel:** Nächtlicher Test-Run Service

```ini
[Unit]
Description=Rezept Tagebuch Nightly Test Run
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/home/gabor/easer_projekte/rezept-tagebuch
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/test/test-and-approve-for-prod.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

**Target:** TEST Container (seaser-rezept-tagebuch-test)
