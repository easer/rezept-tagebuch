# Datenbank und Storage Architektur

**Version:** v25.11.10
**Status:** ✅ Produktiv im Einsatz

---

## 🎯 Überblick

Die Rezept-Tagebuch App verwendet eine **strikte Trennung** zwischen PROD, DEV und TEST Umgebungen:
- Jede Umgebung hat ihren **eigenen Postgres Container**
- Jede Umgebung hat ihre **eigene Datenbank**
- Jede Umgebung hat ihr **eigenes Upload-Verzeichnis**

**⚠️ WICHTIG:** Diese Konfiguration darf **NIEMALS** geändert werden. Container müssen immer auf ihre korrekten DBs und Upload-Verzeichnisse zeigen.

---

## 📦 Container Architektur

### Postgres Container (Datenbanken)

```
┌─────────────────────────────────────────────┐
│  seaser-postgres (PROD)                     │
│  DB: rezepte                                │
│  Volume: data/postgres/                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  seaser-postgres-dev (DEV)                  │
│  DB: rezepte_dev                            │
│  Volume: data/postgres-dev/                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  seaser-postgres-test (TEST)                │
│  DB: rezepte_test                           │
│  Volume: data/postgres-test/                │
└─────────────────────────────────────────────┘
```

### App Container (Flask)

```
┌─────────────────────────────────────────────┐
│  seaser-rezept-tagebuch (PROD)              │
│  Network: seaser-network                    │
│  DB: seaser-postgres → rezepte              │
│  Uploads: data/prod/uploads → /data/uploads │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  seaser-rezept-tagebuch-dev (DEV)           │
│  Network: seaser-network                    │
│  Env: DEV_MODE=true                         │
│  DB: seaser-postgres-dev → rezepte_dev      │
│  Uploads: data/dev/uploads → /data/dev/uploads │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  seaser-rezept-tagebuch-test (TEST)         │
│  Network: seaser-network                    │
│  Env: TESTING_MODE=true                     │
│  DB: seaser-postgres-test → rezepte_test    │
│  Uploads: data/test/uploads → /data/test/uploads │
└─────────────────────────────────────────────┘
```

---

## 📁 Verzeichnisstruktur

```
/home/gabor/easer_projekte/rezept-tagebuch/
│
├── data/                          ← Alle persistenten Daten
│   │
│   ├── postgres/                  ← PROD Postgres Daten
│   ├── postgres-dev/              ← DEV Postgres Daten
│   ├── postgres-test/             ← TEST Postgres Daten
│   │
│   ├── prod/
│   │   └── uploads/               ← PROD Bilder (gemountet zu /data/uploads)
│   │
│   ├── dev/
│   │   └── uploads/               ← DEV Bilder (gemountet zu /data/dev/uploads)
│   │
│   └── test/
│       └── uploads/               ← TEST Bilder (gemountet zu /data/test/uploads)
│
├── app.py                         ← Flask App
├── models.py                      ← SQLAlchemy Models
├── config.py                      ← DB Config (automatische Umgebungs-Erkennung)
└── ...
```

### ⚠️ Wichtig: Alte Verzeichnisse

**NICHT MEHR VERWENDET:**
- `/home/gabor/seaser_uploads/` - War temporär, wurde aufgeräumt
- `data/uploads/` - War alte PROD Location, wurde aufgeräumt
- `data/dev/dev/uploads/` - War Fehler, wurde aufgeräumt

---

## 🔧 Container Start-Commands

### PROD

```bash
podman run -d \
  --name seaser-rezept-tagebuch \
  --network seaser-network \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/prod/uploads:/data/uploads:Z \
  seaser-rezept-tagebuch:latest
```

**Config (config.py):**
- `DEV_MODE=False` (default)
- `TESTING_MODE=False` (default)
- DB: `postgresql://postgres:seaser@seaser-postgres:5432/rezepte`
- Uploads: `/data/uploads/` (UPLOAD_FOLDER aus config.py)

### DEV

```bash
podman run -d \
  --name seaser-rezept-tagebuch-dev \
  --network seaser-network \
  -e DEV_MODE=true \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/dev/uploads:/data/dev/uploads:Z \
  seaser-rezept-tagebuch:dev
```

**Config (config.py):**
- `DEV_MODE=true` (Environment Variable)
- DB: `postgresql://postgres:seaser@seaser-postgres-dev:5432/rezepte_dev`
- Uploads: `/data/dev/uploads/` (UPLOAD_FOLDER aus config.py)

### TEST

```bash
podman run -d \
  --name seaser-rezept-tagebuch-test \
  --network seaser-network \
  -e TESTING_MODE=true \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/test/uploads:/data/test/uploads:Z \
  seaser-rezept-tagebuch:test
```

**Config (config.py):**
- `TESTING_MODE=true` (Environment Variable)
- DB: `postgresql://postgres:test@seaser-postgres-test:5432/rezepte_test`
- Uploads: `/data/test/uploads/` (UPLOAD_FOLDER aus config.py)

---

## 💾 Wie Bilder gespeichert werden

### Speicherung

1. **Upload**: Nutzer/API lädt Bild hoch
2. **Filename**: UUID generiert (z.B. `a600ac6a-cbce-4c23-8cb5-ad58cea2b3fc.jpg`)
3. **Filesystem**: Bild gespeichert in Volume (`data/{env}/uploads/`)
4. **Database**: Nur Filename gespeichert in `recipes.image` Spalte

### Beispiel

```python
# In der DB (recipes Tabelle):
id  | title       | image
----|-------------|----------------------------------------
118 | Apfelkuchen | a600ac6a-cbce-4c23-8cb5-ad58cea2b3fc.jpg

# Im Filesystem:
/home/gabor/easer_projekte/rezept-tagebuch/data/prod/uploads/
└── a600ac6a-cbce-4c23-8cb5-ad58cea2b3fc.jpg  (155 KB)

# Im Container gemountet als:
/data/uploads/a600ac6a-cbce-4c23-8cb5-ad58cea2b3fc.jpg
```

### API Zugriff

```
GET /api/uploads/a600ac6a-cbce-4c23-8cb5-ad58cea2b3fc.jpg
→ Flask sendet Datei aus UPLOAD_FOLDER
→ Nginx Proxy leitet weiter
→ Browser empfängt Bild
```

---

## 🔍 Verifizierung

### Prüfen ob Container korrekt verdrahtet sind

```bash
# PROD Container DB
podman exec seaser-rezept-tagebuch python3 -c \
  "from config import SQLALCHEMY_DATABASE_URI, DEV_MODE; \
   print(f'DEV_MODE: {DEV_MODE}'); \
   print(f'DB: {SQLALCHEMY_DATABASE_URI}')"

# Expected Output:
# DEV_MODE: False
# DB: postgresql://postgres:seaser@seaser-postgres:5432/rezepte

# DEV Container DB
podman exec seaser-rezept-tagebuch-dev python3 -c \
  "from config import SQLALCHEMY_DATABASE_URI, DEV_MODE; \
   print(f'DEV_MODE: {DEV_MODE}'); \
   print(f'DB: {SQLALCHEMY_DATABASE_URI}')"

# Expected Output:
# DEV_MODE: True
# DB: postgresql://postgres:seaser@seaser-postgres-dev:5432/rezepte_dev
```

### Prüfen ob Bilder korrekt gemountet sind

```bash
# PROD Bilder
podman inspect seaser-rezept-tagebuch | grep -A2 "Mounts"
# Expected: data/prod/uploads -> /data/uploads

# DEV Bilder
podman inspect seaser-rezept-tagebuch-dev | grep -A2 "Mounts"
# Expected: data/dev/uploads -> /data/dev/uploads
```

### Prüfen ob Bilder erreichbar sind

```bash
# PROD
podman exec seaser-rezept-tagebuch ls /data/uploads/ | wc -l

# DEV
podman exec seaser-rezept-tagebuch-dev ls /data/dev/uploads/ | wc -l
```

---

## 🧹 Wartung

### Verwaiste Bilder löschen (PROD)

Löscht alle Bilder, die nicht mehr von Rezepten referenziert werden:

```python
podman exec seaser-rezept-tagebuch python3 -c "
from app import app, db, Recipe
import os

with app.app_context():
    # Get all image filenames from DB
    recipes = Recipe.query.all()
    used_images = {r.image for r in recipes if r.image}

    # Get all files in uploads
    upload_dir = '/data/uploads'
    all_files = set(os.listdir(upload_dir))

    # Find orphaned files
    orphaned = all_files - used_images

    # Delete orphaned files
    for filename in orphaned:
        os.remove(os.path.join(upload_dir, filename))

    print(f'Deleted {len(orphaned)} orphaned images')
"
```

### Backup erstellen

```bash
# Datenbank Backup (PROD)
podman exec seaser-postgres pg_dump -U postgres rezepte > backup_$(date +%Y%m%d).sql

# Bilder Backup (PROD)
tar -czf backup_images_$(date +%Y%m%d).tar.gz \
  /home/gabor/easer_projekte/rezept-tagebuch/data/prod/uploads/
```

### Restore

```bash
# Datenbank Restore
cat backup_20251110.sql | \
  podman exec -i seaser-postgres psql -U postgres -d rezepte

# Bilder Restore
tar -xzf backup_images_20251110.tar.gz -C /
```

---

## 🚨 Troubleshooting

### Problem: Container zeigt auf falsche DB

**Symptom:** DEV zeigt gleiche Rezepte wie PROD

**Lösung:**
```bash
# 1. Container stoppen
podman stop seaser-rezept-tagebuch-dev

# 2. Container löschen
podman rm seaser-rezept-tagebuch-dev

# 3. Mit korrekter Config neu starten
podman run -d \
  --name seaser-rezept-tagebuch-dev \
  --network seaser-network \
  -e DEV_MODE=true \
  -v /home/gabor/easer_projekte/rezept-tagebuch/data/dev/uploads:/data/dev/uploads:Z \
  seaser-rezept-tagebuch:dev

# 4. Verifizieren
podman exec seaser-rezept-tagebuch-dev python3 -c \
  "from config import SQLALCHEMY_DATABASE_URI; print(SQLALCHEMY_DATABASE_URI)"
```

### Problem: Bilder werden nicht angezeigt

**Symptom:** Rezept hat image in DB, aber Bild lädt nicht

**Diagnose:**
```bash
# 1. Check DB Entry
podman exec seaser-rezept-tagebuch python3 -c \
  "from app import app, db, Recipe; \
   with app.app_context(): \
     r = Recipe.query.first(); \
     print(f'Image: {r.image}')"

# 2. Check File exists
podman exec seaser-rezept-tagebuch ls -lh /data/uploads/[IMAGE_NAME]

# 3. Check Volume Mount
podman inspect seaser-rezept-tagebuch | grep Mounts -A5
```

**Lösung:** Container mit korrekt gemountetem Volume neu starten (siehe oben)

### Problem: Bilder gehen bei Container-Neustart verloren

**Ursache:** Volume nicht korrekt gemountet

**Lösung:** Siehe "Container Start-Commands" oben - Volume MUSS gemountet sein!

---

## 📚 Siehe auch

- `README.md` - Allgemeine Dokumentation
- `config.py` - Database Config Logik
- `models.py` - SQLAlchemy Models
- `POSTGRESQL-QUICKSTART.md` - Alte Migration Docs (archiviert)
