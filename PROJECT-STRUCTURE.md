# Projekt-Struktur Richtlinien - Rezept-Tagebuch

**Stand:** 06.11.2025
**Version:** 1.0

---

## 🎯 Grundprinzip

**ALLES was zur Rezept-Tagebuch App gehört, MUSS im Projektverzeichnis sein!**

```
/home/gabor/easer_projekte/rezept-tagebuch/
```

Keine App-bezogenen Dateien außerhalb dieses Verzeichnisses!

---

## 📁 Erlaubte Verzeichnisstruktur

### ✅ RICHTIG - Alles im Projekt

```
/home/gabor/easer_projekte/rezept-tagebuch/
├── data/                          # Alle Runtime-Daten
│   ├── prod/
│   │   ├── rezepte.db            # Prod Datenbank
│   │   ├── uploads/              # Prod Uploads
│   │   └── backups/              # Prod Backups
│   └── dev/
│       ├── rezepte.db            # Dev Datenbank
│       ├── uploads/              # Dev Uploads
│       └── backups/              # Dev Backups
├── migrations/                    # Alembic Migrations
├── app.py                        # Backend Code
├── index.html                    # Frontend Code
├── *.sh                          # Deployment Scripts
├── *.md                          # Dokumentation
└── ...
```

### ❌ FALSCH - Außerhalb des Projekts

```
❌ /home/gabor/data/rezept-tagebuch/         # NICHT ERLAUBT
❌ /home/gabor/rezept-data/                  # NICHT ERLAUBT
❌ /var/lib/rezept-tagebuch/                 # NICHT ERLAUBT
❌ /tmp/rezept-*.db                          # NICHT ERLAUBT
```

---

## 📋 Checkliste für neue Dateien/Verzeichnisse

### Vor dem Erstellen einer neuen Datei/Verzeichnis prüfen:

- [ ] Gehört es zur Rezept-Tagebuch App?
- [ ] Kann es im Projektverzeichnis platziert werden?
- [ ] Ist der Pfad relativ zum Projektverzeichnis?
- [ ] Wird es in `.gitignore` eingetragen (falls Runtime-Daten)?

**Wenn JA → Ins Projektverzeichnis!**

---

## 🗂️ Spezielle Verzeichnisse

### data/ (Runtime-Daten, nicht in Git)

**Zweck:** Alle Laufzeit-Daten (DBs, Uploads, Backups)

**Struktur:**
```
data/
├── prod/      # Nur für Production Container
└── dev/       # Nur für Development Container
```

**Regeln:**
- ✅ In `.gitignore` eingetragen
- ✅ Wird NICHT committet
- ✅ Muss in Backups enthalten sein
- ✅ Container mounten nur ihr Environment (prod oder dev)

### migrations/ (Alembic Migrations, in Git)

**Zweck:** Datenbank-Schema-Versionierung

**Regeln:**
- ✅ Wird committet
- ✅ Alle Migrations im Projekt
- ✅ Keine Migrations außerhalb

### Scripts (*.sh, in Git)

**Zweck:** Deployment, Backup, Testing

**Regeln:**
- ✅ Alle Scripts im Projekt-Root
- ✅ Keine Scripts in `/usr/local/bin/` oder anderen System-Verzeichnissen
- ✅ Immer relative Pfade nutzen (außer absolute Projekt-Pfade)

---

## 🐳 Container-Mounts

### ✅ RICHTIG - Projekt-relative Mounts

```bash
# Dev
-v /home/gabor/easer_projekte/rezept-tagebuch/data/dev:/data:Z

# Prod
-v /home/gabor/easer_projekte/rezept-tagebuch/data/prod:/data:Z
```

### ❌ FALSCH - Externe Mounts

```bash
# NICHT VERWENDEN!
-v /home/gabor/data/rezept-tagebuch:/data:Z
-v /var/lib/rezept-data:/data:Z
-v /mnt/rezept-uploads:/uploads:Z
```

---

## 🔧 SystemD Services

**Ausnahme:** SystemD Service-Dateien dürfen außerhalb sein

**Erlaubt:**
```
~/.config/systemd/user/container-seaser-rezept-tagebuch.service
~/.config/systemd/user/container-seaser-rezept-tagebuch-dev.service
```

**Warum?** SystemD erfordert spezifische Pfade für User-Services.

**Regel:** Services werden automatisch von Scripts generiert (via `podman generate systemd`)

---

## 📝 Dokumentation

### Alle Docs im Projekt

**Erlaubt:**
```
/home/gabor/easer_projekte/rezept-tagebuch/
├── README.md
├── DEPLOYMENT.md
├── MIGRATIONS.md
├── PROJECT-STRUCTURE.md     ← Diese Datei
├── GIT-TAG-WORKFLOW.md
└── ...
```

**Nicht erlaubt:**
```
❌ /home/gabor/docs/rezept-tagebuch.md
❌ ~/Desktop/rezept-notes.txt
```

---

## 🚫 Ausnahmen (absolutes Minimum)

### Was darf außerhalb sein:

1. **SystemD User Services** (technische Notwendigkeit)
   - `~/.config/systemd/user/container-seaser-rezept-tagebuch*.service`

2. **Podman Images** (wird automatisch gemanagt)
   - Container Image Storage von Podman selbst

3. **Git Remote** (auf GitHub/GitLab)
   - `git@github.com:easer/rezept-tagebuch.git`

4. **Archive** (nur temporär, nach Migration)
   - `/home/gabor/archive/rezept-*`
   - Sollten nach erfolgreichem Test gelöscht werden

**Das war's!** Alles andere → ins Projektverzeichnis!

---

## ✅ Compliance Check

### Regelmäßig prüfen:

```bash
# Suche nach Rezept-bezogenen Dateien außerhalb des Projekts
find /home/gabor -name "*rezept*" -type f 2>/dev/null | \
  grep -v "easer_projekte/rezept-tagebuch" | \
  grep -v ".cache" | \
  grep -v ".local" | \
  grep -v "systemd/user" | \
  grep -v "archive"
```

**Ergebnis sollte leer sein!**

### Bei Fund:

1. Prüfen ob Datei zur App gehört
2. Wenn JA → Ins Projektverzeichnis verschieben
3. Scripts/Pfade anpassen
4. Diese Richtlinie updaten falls neuer Edge-Case

---

## 🔄 Migration bestehender Dateien

Falls externe Dateien gefunden werden:

1. **Backup erstellen**
   ```bash
   cp <externe-datei> <externe-datei>.backup
   ```

2. **In Projekt verschieben**
   ```bash
   mv <externe-datei> /home/gabor/easer_projekte/rezept-tagebuch/<ziel>
   ```

3. **Scripts anpassen**
   - Alle Referenzen auf neue Pfade ändern

4. **Testen**
   - Dev & Prod Container neu starten
   - Funktionalität prüfen

5. **Alte Backups aufräumen**
   - Nach erfolgreichem Test löschen

---

## 📖 Beispiele

### ❌ FALSCH

```bash
# Backup Script erstellt DB-Backup außerhalb
cp /data/rezepte.db /home/gabor/backups/rezept-backup.db

# Upload-Verzeichnis extern
UPLOAD_DIR="/var/uploads/rezept-tagebuch"

# Config-Datei extern
source /etc/rezept-tagebuch/config.sh
```

### ✅ RICHTIG

```bash
# Backup Script nutzt Projekt-Verzeichnis
./backup-db.sh prod  # Erstellt Backup in ./data/prod/backups/

# Upload-Verzeichnis im Projekt
UPLOAD_DIR="./data/prod/uploads"

# Config-Datei im Projekt
source .env  # Im Projekt-Root
```

---

## 🎓 Warum diese Richtlinie?

### Vorteile:

1. **Einfache Backups**
   - Ein Verzeichnis = gesamte App
   - Kein File-Hunting bei Disaster Recovery

2. **Klare Ownership**
   - Alles im Projekt-Scope
   - Keine versteckten Abhängigkeiten

3. **Portabilität**
   - Projekt auf anderen Server verschieben = `rsync` auf ein Verzeichnis
   - Keine System-weiten Änderungen nötig

4. **Entwicklung**
   - Dev & Prod klar getrennt
   - Keine Konflikte zwischen Environments

5. **Git-Integration**
   - Code & Struktur versioniert
   - Rollback = Git-Checkout + Daten-Restore

6. **Maintenance**
   - Schnell erkennen was zur App gehört
   - Aufräumen = ein Verzeichnis löschen

---

## 🚨 Verstoß gegen Richtlinie

### Was tun bei Verstößen?

1. **Issue erstellen** im GitHub Repo
   - Beschreibung: Welche Datei/Verzeichnis extern?
   - Label: `project-structure`
   - Priorität: `high`

2. **Migration planen** (siehe Issue #9 als Beispiel)
   - Backup erstellen
   - Dateien verschieben
   - Scripts anpassen
   - Testen

3. **Richtlinie erweitern** falls neuer Edge-Case
   - Diese Datei updaten
   - Commit mit Begründung

---

## 📅 Review

**Nächster Review:** 06.12.2025
**Verantwortlich:** Projekt-Maintainer

**Prüfpunkte:**
- [ ] Compliance Check durchführen
- [ ] Archive aufräumen
- [ ] Neue Exceptions prüfen
- [ ] Richtlinie bei Bedarf anpassen

---

**Version History:**
- **v1.0** (06.11.2025) - Initial version nach Issue #9 Migration

---

**Bei Fragen oder Unklarheiten:**
1. Diese Datei konsultieren
2. Issue #9 als Referenz-Beispiel ansehen
3. Bei Unsicherheit: Issue erstellen und diskutieren

**Motto:** *"Wenn es zur App gehört, gehört es ins Projektverzeichnis!"*
