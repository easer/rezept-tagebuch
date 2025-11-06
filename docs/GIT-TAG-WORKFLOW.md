# Git-Tag-basiertes Deployment

Seit Version `rezept_version_05_11_2025_001` werden **nur noch versionierte Git-Tags** auf Production deployed.

## Warum?

✅ **Garantiert**, dass nur committete Snapshots auf Prod landen
✅ Vollständige **Nachvollziehbarkeit** jeder Prod-Version
✅ **Rollback** auf exakte Git-Versionen möglich
✅ Verhindert versehentliche Deployments mit uncommitteten Änderungen
✅ **Laufende Nummer** erlaubt mehrere Releases pro Tag

---

## Tag-Format

**Pattern:** `rezept_version_DD_MM_YYYY_NNN`

**Beispiele:**
- `rezept_version_05_11_2025_001` → zeigt als `v05.11.25-1`
- `rezept_version_05_11_2025_002` → zeigt als `v05.11.25-2`
- `rezept_version_15_12_2025_001` → zeigt als `v15.12.25-1`

**Ungültige Formate** werden abgelehnt:
- ❌ `v1.0.0`
- ❌ `rezept_version_5_11_2025_001` (Tag/Monat muss 2-stellig sein)
- ❌ `rezept_version_05_11_2025_1` (Build muss 3-stellig sein: 001)
- ❌ `version_05_11_2025_001` (muss mit `rezept_version_` beginnen)

---

## Workflow

### 1. Code entwickeln & testen

```bash
# In Dev entwickeln
vim app.py
./scripts/deployment/build-dev.sh

# Testen: http://192.168.2.139:8000/rezept-tagebuch-dev/
```

### 2. Änderungen committen

```bash
git add .
git commit -m "deine message"
```

### 3. Git-Tag erstellen

**Option A: Mit Helper-Script - Auto-Increment (empfohlen)**

```bash
./scripts/deployment/tag-version.sh
# Führt automatisch Tests aus (pytest + E2E)
# Erstellt automatisch Tag: rezept_version_DD_MM_YYYY_NNN
# Findet die nächste freie Nummer für heutiges Datum
# z.B.: rezept_version_05_11_2025_001
```

**Was passiert beim Tag erstellen:**
1. ✅ Prüft ob Working Directory clean ist
2. ✅ Führt pytest Test-Suite aus (27 Tests)
3. ✅ Führt E2E Test aus (Recipe Import)
4. ✅ Erstellt Git-Tag nur wenn alle Tests bestehen

**Option B: Mit Helper-Script - Custom**

```bash
./scripts/deployment/tag-version.sh rezept_version_06_11_2025_001
# Spezifischer Tag für bestimmtes Datum/Build
# Tests werden trotzdem ausgeführt
```

**Option C: Tests überspringen (Notfall)**

```bash
TAG_SKIP_TESTS=1 ./tag-version.sh
# Überspringt alle Tests - nur in Notfällen!
```

**Option D: Manuell (nicht empfohlen)**

```bash
git tag -a rezept_version_05_11_2025_001 -m "Release Notes hier"
# Tests werden NICHT ausgeführt
```

### 4. Auf Prod deployen

```bash
./scripts/deployment/deploy-prod.sh rezept_version_05_11_2025_001
```

**Was passiert:**
1. ✅ Prüft ob Working Directory clean ist (uncommittete Änderungen → Fehler)
2. ✅ Validiert Tag-Format
3. ✅ Prüft ob Git-Tag existiert
4. ✅ Exportiert Git-Tag in temp-Directory
5. ✅ Baut Container-Image **aus dem Git-Tag** (nicht aus Working Directory!)
6. ✅ Erstellt automatisch DB-Backup
7. ✅ Führt Migrations durch
8. ✅ Startet Prod-Container neu

### 5. (Optional) Tag pushen

```bash
git push origin rezept_version_05_11_2025_001
```

---

## Rollback

```bash
# Verfügbare Tags anzeigen
git tag | grep rezept_version

# Zu alter Version zurück
./scripts/deployment/rollback.sh rezept_version_04_11_2025
```

**Hinweis:** Das Container-Image für den Tag muss existieren. Wenn nicht, erst nochmal deployen:

```bash
./scripts/deployment/deploy-prod.sh rezept_version_04_11_2025
```

---

## Sicherheits-Features

### Dirty-Check

Wenn du versuchst zu deployen mit uncommitteten Änderungen:

```bash
$ ./deploy-prod.sh rezept_version_05_11_2025

❌ Working Directory ist nicht clean!

 M app.py
?? test.py

Du musst alle Änderungen committen, bevor du auf Prod deployen kannst.
```

### Tag-Format-Validierung

```bash
$ ./deploy-prod.sh v1.0.0

❌ Ungültiges Tag-Format!
   Erwartet: rezept_version_DD_MM_YYYY
   Beispiel: rezept_version_05_11_2025
```

### Git-Tag-Existenz-Check

```bash
$ ./deploy-prod.sh rezept_version_99_99_2099

❌ Git-Tag 'rezept_version_99_99_2099' existiert nicht!

Verfügbare Tags:
  rezept_version_05_11_2025

Neuen Tag erstellen:
  ./tag-version.sh
```

---

## Übersicht: Alle Commands

| Command | Beschreibung |
|---------|-------------|
| `./tag-version.sh` | Erstellt Git-Tag mit heutigem Datum |
| `./tag-version.sh rezept_version_DD_MM_YYYY` | Erstellt Git-Tag mit custom Datum |
| `./deploy-prod.sh <GIT_TAG>` | Deployed spezifischen Git-Tag auf Prod |
| `./rollback.sh <GIT_TAG>` | Rollback zu alter Version |
| `git tag \| grep rezept_version` | Alle Tags anzeigen |
| `podman images \| grep rezept_version` | Alle Container-Images anzeigen |

---

## Beispiel-Session

```bash
# 1. Code ändern
vim app.py

# 2. In Dev testen
./scripts/deployment/build-dev.sh
# Test auf: http://192.168.2.139:8000/rezept-tagebuch-dev/

# 3. Committen
git add app.py
git commit -m "feat: neue Feature XYZ"

# 4. Tag erstellen (Auto-Increment)
./scripts/deployment/tag-version.sh
# Auto-generierter Tag: rezept_version_05_11_2025_001
# Message: Release 05.11.2025 Build 1 - Feature XYZ

# 5. Deployen
./scripts/deployment/deploy-prod.sh rezept_version_05_11_2025_001

# ✅ Live auf: http://192.168.2.139:8000/rezept-tagebuch/
# ✅ Version Badge zeigt: v05.11.25-1

# 6. (Optional) Tag pushen
git push origin rezept_version_05_11_2025_001
```

---

## FAQ

**Q: Kann ich mehrere Tags pro Tag erstellen?**
A: Ja! Genau dafür ist die laufende Nummer da:
```bash
./scripts/deployment/tag-version.sh  # Erstellt automatisch _001, _002, _003 etc.
```

**Q: Was passiert mit uncommitteten Änderungen?**
A: Das Script blockt das Deployment. Du **musst** erst committen.

**Q: Kann ich einen Tag löschen?**
A: Ja, aber nur wenn er noch nicht deployed wurde:
```bash
git tag -d rezept_version_05_11_2025_001
```

**Q: Wie finde ich heraus, welche Version aktuell auf Prod läuft?**
A:
```bash
podman inspect seaser-rezept-tagebuch | grep Image
```

**Q: Kann ich dev-Container auch mit Tags deployen?**
A: Nein. Dev nutzt weiterhin den `:dev` Tag und baut direkt aus dem Working Directory.

---

**Erstellt:** 05.11.2025
**Version:** Git-Tag-basiertes Deployment v1
