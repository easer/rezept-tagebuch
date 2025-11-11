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
