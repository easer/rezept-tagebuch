# Changelog - Rezept-Tagebuch

All notable changes to this project will be documented in this file.

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
