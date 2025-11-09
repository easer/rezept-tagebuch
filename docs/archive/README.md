# Archivierte Dokumentation

Dieses Verzeichnis enthält veraltete oder historische Dokumentation, die nicht mehr aktiv verwendet wird.

## 📦 Archivierte Dateien

### POSTGRESQL-MIGRATION.md
**Status**: ✅ Abgeschlossen am 2025-11-09
**Zweck**: Dokumentiert die einmalige Migration von SQLite zu PostgreSQL
**Grund für Archivierung**: Migration ist abgeschlossen, wird nicht mehr benötigt

### MIGRATION_WORKFLOW.md
**Status**: ⚠️ Deprecated am 2025-11-09
**Zweck**: Alter Tag-basierter Workflow für Deployments
**Grund für Archivierung**: Ersetzt durch [IMPROVED_WORKFLOW.md](../IMPROVED_WORKFLOW.md)
**Unterschiede**:
- Alt: Git-Tag Parameter für test-migration.sh erforderlich
- Neu: Nutzt HEAD (Working Directory), Commit-Hash Freigabe

## 📚 Aktuelle Dokumentation

Siehe [../IMPROVED_WORKFLOW.md](../IMPROVED_WORKFLOW.md) für den aktuellen Workflow.
