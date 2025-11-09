# Changelog - Rezept-Tagebuch

All notable changes to this project will be documented in this file.

## [rezept_version_09_11_2025_001] - 2025-11-09

### Added - Alembic Migration Workflow
- **Automatisierte Migration-Pipeline** für TEST → DEV → PROD
  - `test-migration.sh`: Migration auf TEST mit automatischen Tests
  - `deploy-prod.sh`: Erweitert um automatische Alembic Migration
  - Alembic Config für TEST/PROD Umgebungen
  - Migration Tests in `tests/test_migrations.py`
- **Dokumentation**
  - `docs/MIGRATION_WORKFLOW.md`: Kompletter Workflow Guide
  - README.md aktualisiert mit Migration-Workflow

### Changed - Database Schema
- **recipes.imported_at → recipes.erstellt_am**
  - Spalte umbenannt von `imported_at` (DATE) zu `erstellt_am` (TIMESTAMP)
  - Wird jetzt für ALLE Rezepte gesetzt (nicht nur imports)
  - DEFAULT CURRENT_TIMESTAMP für automatische Population
  - Frontend zeigt Erstellungsdatum unter "Erstellt von" Label
  - Migration: `20251109_1100_002_rename_imported_at_to_erstellt_am.py`

### Fixed
- PROD Container mit altem Code nach Migration
  - Deployment-Process erstellt jetzt automatisch Backup vor Migration
  - Alembic läuft in separatem Container vor App-Deployment

### Technical
- Alembic im Container integriert
- `migrations/env.py` angepasst für PostgreSQL Support
- Containerfile kopiert jetzt `migrations/` und `alembic.ini`

## [rezept_version_07_11_2025_001] - 2025-11-07

### Added
- Meat-free filter für TheMealDB Daily Import
  - Neue Konfiguration: `themealdb-config.json` mit `excludeMeatCategories`
  - Retry-Mechanismus (bis zu 5 Versuche) für fleischfreie Rezepte
  - Logging für alle Versuche und Auswahlgründe

### Fixed
- Test-Infrastruktur Verbesserungen
  - Separate Test-Datenbank (`/data/test/rezepte.db`)
  - Test-Container auf separatem Port (8001)
  - Cleanup-Fixtures für Diary Entries
- API Bug: Fehlender `dish_name` bei GET `/api/diary` Endpoint
  - Field jetzt korrekt included in Query
  - Test Coverage für Diary CRUD erweitert

### Changed
- `.gitignore`: `.claude/` Verzeichnis excluded

## [rezept_version_06_11_2025_006] - 2025-11-06

### Fixed - Infrastructure & Project Organization

#### Database & Artifact Consolidation (Issue #9)
- Alle Datenbanken und Runtime-Daten in Projektverzeichnis verschoben
- Neue Struktur: `./data/prod/` und `./data/dev/` im Projekt-Root
- Volume Mounts in `build-dev.sh` und `deploy-prod.sh` aktualisiert
- Backup/Restore Scripts (`backup-db.sh`, `restore-db.sh`) mit neuen Pfaden
- Alte Verzeichnisse archiviert:
  - `/home/gabor/data/rezept-tagebuch/` → `~/archive/rezept-tagebuch-old-20251106`
  - `/home/gabor/easer_projekte/rezept-tagebuch-data/` → `~/archive/rezept-tagebuch-data-old-20251106`
  - `/home/gabor/easer_projekte/rezept-data/` → `~/archive/rezept-data-old-20251106`
- `.gitignore` erweitert um `data/` (Runtime-Daten nicht in Git)

### Added - Documentation

#### PROJECT-STRUCTURE.md (NEU)
- Richtlinien für Projekt-Organisation erstellt
- Regel: "Alles was zur App gehört, MUSS im Projektverzeichnis sein"
- Dokumentierte Ausnahmen:
  - SystemD User Services (technische Notwendigkeit)
  - Nginx Reverse Proxy (Shared Resource für mehrere Apps)
  - Podman Images (automatisch gemanagt)
  - Git Remote
- Compliance Check Script für Validierung
- Migration Guidelines basierend auf Issue #9
- Nginx-Dokumentation als Shared Resource:
  - Location: `/home/gabor/easer_projekte/nginx-proxy-oauth2.conf`
  - Update-Prozess mit Commands
  - Routes für Rezept-Tagebuch (prod + dev)
  - Warnung: Nginx-Änderungen betreffen ALLE Apps

### Changed - Documentation Updates

#### README.md
- Volume Mount Pfade aktualisiert (Tabelle `data/prod/` und `data/dev/`)
- Deployment-Workflow auf Git-Tag Format angepasst
  - Von: `./scripts/deployment/deploy-prod.sh 25.11.05`
  - Zu: `./scripts/deployment/deploy-prod.sh rezept_version_06_11_2025_001`
- Rollback-Beispiele mit Git-Tag Format

#### DEPLOYMENT.md
- Container-Übersicht Tabelle: Volume Mounts korrigiert
- Alle Deployment-Beispiele auf Git-Tag Format aktualisiert
- Backup-Sektion: Referenz zu `backup-db.sh` Script statt manuellem `cp`
- **Branch-Strategie geklärt**: Kein separater `production` Branch mehr
  - Alle Deployments erfolgen von `main` Branch mit Git-Tags
  - Entfernung der veralteten "Workflow 2a: Production Release (mit Branch-Merge)"
  - Klarstellung: Nur `main` + Git-Tags werden verwendet

#### UX-GUIDE.md
- Ersetzt veraltete "Globale Suchleiste" Dokumentation
- Neue Sektion: "Search Panel (Slide-In von rechts)"
- Dokumentiert aktuelles Search Panel System mit Plus-Symbol
- Referenz zu SEARCH-PANEL.md für vollständige Implementierung

### Technical Notes

#### Consistency Fixes
- Git-Tag Format standardisiert: `rezept_version_DD_MM_YYYY_NNN`
- Alle Dokumentations-Dateien auf konsistente Pfade aktualisiert
- Deployment-Workflow eindeutig dokumentiert (main Branch + Git-Tags)

---

## [Unreleased] - 2025-11-04

### Added - TODO Liste UX Verbesserungen

#### Swipe-to-Delete Geste
- TODOs können nun durch Wischen nach links gelöscht werden
- Schwellwert: -100px mit 10px Mindestbewegung verhindert versehentliches Löschen
- Visuelles Feedback: Roter Hintergrund mit "Löschen" Text
- Support für Touch und Mouse Events (Mobile + Desktop)

#### Prioritäten-Visualisierung mit Pastellfarben
- Entfernung der drei separaten Prioritäts-Sektionen
- Neue farbige Border-Markierung für Prioritäten:
  - Priorität I (Hoch): Rosa Pastell (#FFB5C0)
  - Priorität II (Mittel): Gelb Pastell (#FFE66D)
  - Priorität III (Niedrig): Blau Pastell (#AED9E0)
- Automatische Sortierung nach Priorität (1 → 2 → 3)

#### Kompakte TODO-Darstellung
- Feste Höhe von 56px für alle TODO-Items
- Maximale 2 Zeilen Text mit Ellipsis (`-webkit-line-clamp: 2`)
- Vollständiger Text im Detail-View verfügbar

#### TODO Detail-View
- Click auf TODO öffnet Slide-Panel mit vollständiger Ansicht
- In-Place Bearbeitung (Beschreibung, Priorität, Status)
- Löschen-Funktion mit Bestätigung
- Neuer API-Endpoint: `GET /api/todos/<id>`

### Added - Globale UI Verbesserungen

#### Sticky Header & Scrolling Layout
- Header, Tabs und Suchleiste bleiben beim Scrollen fixiert
- Nur Content-Bereich ist scrollbar
- Flexbox-basierte Architektur mit `height: 100vh`
- Optimale Raumnutzung auf allen Bildschirmgrößen

#### Floating Action Button (FAB)
- Globaler Plus-Button ersetzt individuelle "Neu"-Buttons
- Position: Fixed bottom-right (30px Abstand)
- Context-aware: Passt sich aktuellem Tab an
  - Tagebuch: Öffnet "Neuer Eintrag" Dialog
  - Rezepte: Öffnet "Neues Rezept" Dialog
  - TODOs: Öffnet "Neues TODO" Dialog
- Smooth hover-Animation mit Rotation

#### Globale Kontext-Suche
- Eine universelle Suchleiste für alle Tabs
- Automatische Anpassung an aktiven Tab:
  - Tagebuch: Sucht in Gericht, Notizen, Rezept
  - Rezepte: Sucht in Titel, Notizen
  - TODOs: Filtert TODO-Beschreibungen
- Suchfeld wird beim Tab-Wechsel automatisch geleert
- Deaktivierte Browser-Autofill für bessere UX

#### Header-Spacing Optimierung
- Reduzierter padding-top: 40px (vorher 70px)
- Bessere visuelle Balance zwischen Header und Tabs
- Verhindert Überlappung mit "Abmelden" Button

### Fixed

#### Input-Field Focus Issues
- Behoben: Cursor erschien beim ersten Click außerhalb des Feldes
- Behoben: Browser-Autofill-Dropdown störte zweiten Click
- Lösung: `autocomplete="off"`, `autocorrect="off"`, `autocapitalize="off"`, `spellcheck="false"`
- Verbesserte z-index Hierarchie für korrekte Layering

#### Swipe-Geste Sensitivität
- Behoben: TODOs wurden bei einfachem Touch gelöscht
- Hinzugefügt: `hasMoved` Flag mit 10px Schwellwert
- Initialisierung von `currentX = startX` verhindert falsche Berechnungen
- Erhöhung des Delete-Threshold von -80px auf -100px

### Changed

#### API Erweiterungen
- Neuer Endpoint: `GET /api/todos/<int:todo_id>` für einzelne TODO-Abfrage
- Unterstützt Detail-View und Bearbeitungsfunktion

#### CSS Architektur
- Neues z-index Management:
  - Header: 10
  - Global Search: 50
  - Floating Action Button: 100
  - Modals: 1000
- Flexbox-Layout für Container-Hierarchie
- Touch-Action Optimierung für Swipe-Gesten

### Documentation

#### UX-GUIDE.md Aktualisierungen
- Neuer Abschnitt: "TODO Liste UX Pattern"
  - Swipe-to-Delete Implementierung
  - Prioritäten mit Pastellfarben
  - Kompakte Darstellung
  - Detail-View Pattern
- Neuer Abschnitt: "Sticky Header & Scrolling Layout"
  - Flexbox-Architektur
  - Globale Suchleiste Best Practices
  - Floating Action Button Pattern
- Neuer Abschnitt: "Globale Kontext-Suche"
  - Tab-basierte Filterlogik
  - Autocomplete-Deaktivierung
- Erweiterte Entwicklungs-Workflow Checkliste (8-10 Punkte)

---

## Versionshistorie

### v2.1 - Initial Release mit Alembic Migrations
- Migration-System: Alembic 1.13.1
- Schema-Versionierung und Rollback-Support
- Automatische Migrations bei Prod-Deployment
- Backup-System mit Migration-Version-Tracking

### v2.0 - Multi-Environment Setup
- Production und Development Umgebungen
- Nginx Reverse Proxy Integration
- OAuth2 Authentifizierung
- Systemd Service Management

### v1.0 - Initial Release
- Tagebuch-Einträge mit Bildern
- Rezept-Verwaltung
- TODO-Liste mit Prioritäten
- Rating-System für Rezepte
- Responsive Design für Mobile
