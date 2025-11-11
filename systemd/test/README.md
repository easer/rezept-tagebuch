# TEST Systemd Services

**Target:** TEST Container (seaser-rezept-tagebuch-test)
**Port:** 8001
**Env Var:** `TESTING_MODE=true`

---

## Status

Aktuell keine TEST-spezifischen systemd Services.

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
