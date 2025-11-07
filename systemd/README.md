# Systemd Services - Rezept-Tagebuch

**Location:** User-Services (`~/.config/systemd/user/`)
**Type:** Systemd Timer (wie Cron, aber besser)

---

## 🎯 Übersicht

Diese Services werden als **User-Services** ausgeführt (nicht als System-Services), da die Rezepte-App auch als User-Service läuft.

---

## ⏰ Daily Import Timer

### Dateien

- `rezept-daily-import.service` - Service-Definition
- `rezept-daily-import.timer` - Timer-Definition

### Funktion

Lädt täglich um **06:00 Uhr UTC** ein vegetarisches Rezept von TheMealDB herunter.

**Was passiert:**
1. Timer triggert um 06:00 Uhr
2. Wrapper-Script `daily-import.sh` wird ausgeführt
3. Script ruft `/api/recipes/daily-import?strategy=by_category&value=Vegetarian` auf
4. Bei Ablehnung (Fleisch-Rezept): Automatischer Retry (bis zu 10x)
5. Rezept wird in Prod-DB gespeichert
6. Alte Imports werden aufgeräumt (cleanup-old-imports)

**Meat-Filter Protection:**
- Backend validiert Kategorie vor dem Speichern
- Fleisch-Kategorien (Beef, Chicken, Lamb, Pork, Goat, Seafood) werden abgelehnt
- Wrapper-Script wiederholt automatisch bei Ablehnung
- Maximale Versuche: 10 (mit 2 Sekunden Delay)

### Konfiguration

**Timer-Schedule:**
```ini
OnCalendar=*-*-* 06:00:00
Persistent=true
```

- `OnCalendar=*-*-* 06:00:00` → Täglich um 06:00 Uhr UTC
- `Persistent=true` → Verpasste Runs werden nachgeholt

**Service-Execution:**
```ini
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Vegetarian
StandardOutput=journal
StandardError=journal
```

**Was das Script macht:**
- Ruft API mit Retry-Logik auf
- Bis zu 10 Versuche bei Fleisch-Ablehnung
- 2 Sekunden Delay zwischen Versuchen
- Cleanup nach erfolgreichem Import
- Logs erscheinen in systemd journal

---

## 🚀 Installation

### Service installieren

```bash
cd /home/gabor/easer_projekte/rezept-tagebuch

# Dateien nach systemd User-Verzeichnis kopieren
cp systemd/rezept-daily-import.service ~/.config/systemd/user/
cp systemd/rezept-daily-import.timer ~/.config/systemd/user/

# Systemd neu laden
systemctl --user daemon-reload

# Timer aktivieren (auto-start nach Boot)
systemctl --user enable rezept-daily-import.timer

# Timer starten
systemctl --user start rezept-daily-import.timer
```

### Service deinstallieren

```bash
# Timer stoppen
systemctl --user stop rezept-daily-import.timer

# Timer deaktivieren
systemctl --user disable rezept-daily-import.timer

# Dateien löschen
rm ~/.config/systemd/user/rezept-daily-import.{service,timer}

# Systemd neu laden
systemctl --user daemon-reload
```

---

## 🔍 Status & Monitoring

### Timer-Status prüfen

```bash
# Timer-Status
systemctl --user status rezept-daily-import.timer

# Alle Timer anzeigen
systemctl --user list-timers

# Nur rezept-Timer
systemctl --user list-timers | grep rezept
```

**Output:**
```
NEXT                        LEFT LAST                           PASSED UNIT
Sat 2025-11-08 06:00:00 UTC 21h  Fri 2025-11-07 06:00:35 UTC    2h ago rezept-daily-import.timer
```

### Service-Logs ansehen

```bash
# Service-Logs (letzter Run)
journalctl --user -u rezept-daily-import.service

# Mit Timestamps
journalctl --user -u rezept-daily-import.service --since today

# Live-Logs (beim nächsten Run)
journalctl --user -u rezept-daily-import.service -f
```

### Manuell triggern (zum Testen)

```bash
# Service manuell ausführen
systemctl --user start rezept-daily-import.service

# Logs live verfolgen
journalctl --user -u rezept-daily-import.service -f

# Oder direkt Script testen
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Vegetarian
```

### Retry-Logik überwachen

Das Wrapper-Script loggt jeden Retry-Versuch:

```bash
# Letzte Import-Versuche ansehen
journalctl --user -u rezept-daily-import.service --since today

# Beispiel-Output:
# Attempt 1/10: Fetching recipe...
# ⚠️ Recipe rejected: 'Beef Wellington' (category: Beef)
# Retrying in 2s...
# Attempt 2/10: Fetching recipe...
# ✅ Success! Meat-free recipe imported.
# Imported: Mushroom Risotto
```

---

## ⚙️ Import-Strategien

Der Daily-Import unterstützt verschiedene Strategien über das Wrapper-Script:

### 1. By Category (Standard)

```bash
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Vegetarian
```

Nur vegetarische Rezepte. Meat-Filter schützt vor versehentlichem Fleisch-Import.

### 2. Random (mit Meat-Filter)

```bash
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh random
```

Komplett zufälliges Rezept. Fleisch-Rezepte werden automatisch abgelehnt und es wird erneut versucht (bis zu 10x).

### 3. By Category (andere Kategorien)

```bash
# Desserts (fleischfrei)
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Dessert

# Vegan
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Vegan

# Pasta (fleischfrei)
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Pasta
```

### 4. By Area

```bash
# Italienische Rezepte
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_area Italian

# Indische Rezepte
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_area Indian

# Thai-Rezepte
/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_area Thai
```

**Wichtig:** Bei Area-Strategie kann trotzdem Fleisch vorkommen! Der Meat-Filter lehnt diese dann ab und versucht es erneut.

### Strategie ändern

**Option 1: Hauptservice ändern**

Bearbeite `~/.config/systemd/user/rezept-daily-import.service`:

```ini
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_area Italian
```

Dann:
```bash
systemctl --user daemon-reload
systemctl --user restart rezept-daily-import.timer
```

**Option 2: Zusätzlichen Service erstellen (siehe unten)**

---

## 🔧 Zusätzliche Services erstellen

Du kannst mehrere Services für verschiedene Strategien erstellen:

### Beispiel: Dessert-Service (wöchentlich)

1. **Service-Datei erstellen:**

```bash
cat > ~/.config/systemd/user/rezept-dessert-import.service <<'EOF'
[Unit]
Description=Rezept Tagebuch Weekly Dessert Import
After=network.target seaser-rezept-tagebuch.service

[Service]
Type=oneshot
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_category Dessert
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

2. **Timer-Datei erstellen:**

```bash
cat > ~/.config/systemd/user/rezept-dessert-import.timer <<'EOF'
[Unit]
Description=Rezept Tagebuch Weekly Dessert Timer
Requires=rezept-dessert-import.service

[Timer]
OnCalendar=Sun 18:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

3. **Aktivieren:**

```bash
systemctl --user daemon-reload
systemctl --user enable rezept-dessert-import.timer
systemctl --user start rezept-dessert-import.timer
```

### Beispiel: Italienisch-Service (zweimal pro Woche)

```bash
# Service
cat > ~/.config/systemd/user/rezept-italian-import.service <<'EOF'
[Unit]
Description=Rezept Tagebuch Italian Import
After=network.target seaser-rezept-tagebuch.service

[Service]
Type=oneshot
ExecStart=/home/gabor/easer_projekte/rezept-tagebuch/scripts/daily-import.sh by_area Italian
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Timer (Mittwoch und Samstag um 12:00 UTC)
cat > ~/.config/systemd/user/rezept-italian-import.timer <<'EOF'
[Unit]
Description=Rezept Tagebuch Italian Timer
Requires=rezept-italian-import.service

[Timer]
OnCalendar=Wed,Sat 12:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable rezept-italian-import.timer
systemctl --user start rezept-italian-import.timer
```

### Alle Timer anzeigen

```bash
systemctl --user list-timers | grep rezept
```

**Output:**
```
NEXT                        LEFT     LAST                        PASSED  UNIT
Wed 2025-11-08 06:00:00 UTC 18h left Tue 2025-11-07 06:00:35 UTC 3h ago rezept-daily-import.timer
Wed 2025-11-08 12:00:00 UTC 1d left  -                           -      rezept-italian-import.timer
Sun 2025-11-11 18:00:00 UTC 4d left  -                           -      rezept-dessert-import.timer
```

---

## 🐛 Troubleshooting

### Problem: Timer läuft nicht nach Server-Neustart

**Ursache:** User-Services starten erst nach User-Login

**Lösung:** Lingering aktivieren

```bash
# Lingering aktivieren (User-Services laufen auch ohne Login)
sudo loginctl enable-linger gabor

# Prüfen ob aktiv
loginctl show-user gabor | grep Linger
# Output: Linger=yes
```

### Problem: Service failed

```bash
# Logs prüfen
journalctl --user -u rezept-daily-import.service --since today

# Häufige Fehler:
# - Container läuft nicht
# - API nicht erreichbar
# - Netzwerk-Probleme
```

**Check:**
```bash
# Container läuft?
podman ps | grep seaser-rezept-tagebuch

# API erreichbar?
curl http://localhost:8000/rezept-tagebuch/
```

### Problem: Verpasste Runs werden nicht nachgeholt

**Ursache:** `Persistent=true` fehlt oder Server war zu lange aus

**Check:**
```bash
# Timer-Config prüfen
systemctl --user cat rezept-daily-import.timer | grep Persistent

# Sollte sein: Persistent=true
```

---

## 📝 Best Practices

### 1. User-Service statt System-Service

```bash
# ✅ Richtig: User-Service
systemctl --user enable rezept-daily-import.timer

# ❌ Falsch: System-Service (benötigt root)
sudo systemctl enable rezept-daily-import.timer
```

**Warum?** Rezepte-App läuft als User, nicht als Root.

### 2. Lingering aktivieren

```bash
# Damit User-Services auch ohne Login laufen
sudo loginctl enable-linger gabor
```

### 3. Logs regelmäßig prüfen

```bash
# Jeden Monat kurz prüfen ob Timer läuft
systemctl --user status rezept-daily-import.timer
```

### 4. Test nach Änderungen

```bash
# Nach Service-Änderung manuell testen
systemctl --user start rezept-daily-import.service

# Logs prüfen
journalctl --user -u rezept-daily-import.service --since "5 minutes ago"
```

---

## 🔗 Weiterführende Links

- **API-Endpoint:** `/api/recipes/daily-import` in `app.py`
- **TheMealDB Config:** `docs/THEMEALDB-CONFIG.md`
- **Systemd Timer Doku:** `man systemd.timer`
- **Journalctl Doku:** `man journalctl`

---

**Erstellt:** 2025-11-07
**Version:** 1.0
**Maintainer:** Rezept-Tagebuch DevOps
