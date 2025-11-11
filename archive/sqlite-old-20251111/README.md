# SQLite Legacy Files Archive

**Archiviert am:** 2025-11-11
**Grund:** Migration von SQLite zu PostgreSQL abgeschlossen

## Archivierte Dateien

### SQLite-Datenbanken
- `rezepte.db` - Letzte SQLite PROD-Datenbank (Test-Daten, 28 KB)
- `rezepte.db-shm`, `rezepte.db-wal` - SQLite WAL-Dateien
- `rezept_tagebuch.db` - Leere Legacy-Datenbank

### Backup-Datenbanken (backups/)
11 SQLite-Backup-Dateien aus der Migrations-Zeit (06.11. - 07.11.2025):
- `rezepte-20251106-*.db` - Verschiedene Migrations-Backups
- `rezepte-20251107-*.db` - Finales Backup vor PostgreSQL-Migration

### Legacy-Code
- `app_old_sqlite.py` - Alte Flask-App mit direktem SQLite-Support
- `app_new.py` - Übergangs-Version mit SQLAlchemy

### Migrations-Scripts
- `migrate-sqlite-to-postgres.py` - Migrations-Tool
- `migrate-data-to-postgres.py` - Daten-Import-Tool
- `export-sqlite-data.py` - SQLite Export-Tool

## Aktuelle Architektur

Die Rezept-Tagebuch-App nutzt jetzt ausschließlich **PostgreSQL**:
- **PROD:** seaser-postgres (rezepte)
- **DEV:** seaser-postgres-dev (rezepte_dev)
- **TEST:** seaser-postgres-test (rezepte_test)

## Wiederherstellung

Falls SQLite-Daten benötigt werden:
1. Alte Datenbank aus diesem Archiv kopieren
2. `export-sqlite-data.py` nutzen um Daten zu exportieren
3. Bei Bedarf mit `migrate-data-to-postgres.py` nach PostgreSQL migrieren

**Achtung:** Diese Dateien sind nur als Backup gedacht. Die aktive App unterstützt kein SQLite mehr.

## Archivierte Database-Scripts

### Migration-Scripts (veraltet)
- `migrate.sh` - Alembic-Wrapper für SQLite-Migrationen
- `reset-and-migrate-postgres.sh` - SQLite→PostgreSQL One-Time Migration
- `schema-postgres.sql` - Initiales PostgreSQL Schema (ersetzt durch Alembic)

Diese Scripts waren für die Migration von SQLite zu PostgreSQL gedacht und werden nicht mehr benötigt.

### Aktive Database-Scripts (weiterhin in scripts/database/)
- `backup-db.sh` - PostgreSQL Backup-Tool
- `restore-db.sh` - PostgreSQL Restore-Tool
- `test-migration.sh` - Test-Migrations-Tool

## Update 2025-11-11 (zweite Bereinigung)

### Weitere archivierte Scripts
- `backup-db.sh` - SQLite-basiertes Backup-Tool (nicht kompatibel mit PostgreSQL)
- `restore-db.sh` - SQLite-basiertes Restore-Tool (nicht kompatibel mit PostgreSQL)

Diese Scripts arbeiteten mit SQLite .db Dateien und müssen für PostgreSQL neu geschrieben werden:
- PostgreSQL Backups: `pg_dump` (SQL-Dumps)
- PostgreSQL Restore: `psql` (SQL-Import)
- Container-basiert: `podman exec seaser-postgres pg_dump ...`

### Verbleibende aktive Scripts (scripts/database/)
- `test-db-migration-with-clean-commit-for-prod.sh` - PostgreSQL Test-Migration-Workflow (umbenannt von test-migration.sh)

## Update 2025-11-11 (dritte Bereinigung)

### Weitere archivierte Scripts
- `run-tests-isolated.sh` - SQLite-basiertes Test-Script (Zeile 27-30: nutzt `./data/test/rezepte.db`)

Dieses Script ist veraltet, da es:
- SQLite Test-Datenbank nutzt (PostgreSQL hat keine .db Dateien)
- DEV Container mit TESTING_MODE startet (nicht mehr nötig mit separatem TEST Container)
- Test-DB manuell löscht (PostgreSQL nutzt Container-basierte DBs)

Moderne Test-Strategie:
- Separater TEST Container mit eigener PostgreSQL DB
- Migration-Workflow für PROD-Freigabe
- pytest gegen TEST Container (Port 8001)

## Update 2025-11-11 (vierte Bereinigung)

### Git Hooks Script archiviert
- `install-git-hooks.sh` - Git Pre-Commit Hook Installer (veraltet)

Dieses Script ist veraltet, da es:
- DEV Container prüft statt TEST Container (Zeile 34: `seaser-rezept-tagebuch-dev`)
- Veraltete Pfade nutzt (Zeile 39: `./scripts/deployment/build-dev.sh`)
- Nicht installiert ist (nur .sample Dateien in .git/hooks/)

**Status:** Keine aktiven Git Hooks installiert im Projekt
