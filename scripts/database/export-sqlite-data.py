#!/usr/bin/env python3
"""
Export SQLite data to SQL INSERT statements for PostgreSQL
"""

import sqlite3
import sys

def quote_value(val, column_type=None):
    """Quote value for SQL"""
    if val is None:
        return 'NULL'
    elif column_type == 'boolean':
        # Convert SQLite 0/1 to PostgreSQL boolean
        if isinstance(val, str):
            val = int(val) if val.isdigit() else val
        return 'true' if val else 'false'
    elif isinstance(val, bool):
        return 'true' if val else 'false'
    elif isinstance(val, (int, float)):
        return str(val)
    else:
        # Escape single quotes and backslashes
        val = str(val).replace("\\", "\\\\").replace("'", "''")
        return f"'{val}'"

def export_table(conn, table_name, columns, column_types=None):
    """Export table data as INSERT statements"""
    cursor = conn.cursor()
    # SELECT specific columns in the order we want them
    select_cols = ', '.join(columns)
    cursor.execute(f"SELECT {select_cols} FROM {table_name} ORDER BY id")
    rows = cursor.fetchall()

    if column_types is None:
        column_types = [None] * len(columns)

    print(f"-- Migrating {table_name} ({len(rows)} rows)")
    for row in rows:
        values = [quote_value(val, col_type) for val, col_type in zip(row, column_types)]
        cols = ', '.join(columns)
        vals = ', '.join(values)
        print(f"INSERT INTO {table_name} ({cols}) VALUES ({vals});")

    # Update sequence
    print(f"SELECT setval('{table_name}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table_name}));")
    print()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 export-sqlite-data.py <sqlite_db_path>")
        sys.exit(1)

    db_path = sys.argv[1]
    conn = sqlite3.connect(db_path)

    print("-- SQLite to PostgreSQL Data Export")
    print("-- Generated:", db_path)
    print()

    # Export users
    export_table(conn, 'users',
                 ['id', 'email', 'name', 'avatar_color', 'created_at'])

    # Export recipes
    export_table(conn, 'recipes',
                 ['id', 'title', 'image', 'notes', 'duration', 'rating',
                  'user_id', 'is_system', 'auto_imported', 'imported_at',
                  'created_at', 'updated_at'],
                 [None, None, None, None, None, None, None,
                  'boolean', 'boolean', None, None, None])

    # Export todos
    export_table(conn, 'todos',
                 ['id', 'text', 'priority', 'completed', 'user_id',
                  'created_at', 'updated_at'],
                 [None, None, None, 'boolean', None, None, None])

    # Export diary_entries (NOTE: SQLite column order is different!)
    # SQLite: id, recipe_id, date, notes, images, created_at, updated_at, dish_name, user_id
    # PostgreSQL: id, recipe_id, date, notes, images, dish_name, user_id, created_at, updated_at
    # Fix orphaned recipe references: Check if recipe_id exists, else set to NULL
    print("-- Migrating diary_entries (with FK validation)")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            d.id,
            CASE WHEN r.id IS NULL THEN NULL ELSE d.recipe_id END as recipe_id,
            d.date, d.notes, d.images, d.dish_name, d.user_id,
            d.created_at, d.updated_at
        FROM diary_entries d
        LEFT JOIN recipes r ON d.recipe_id = r.id
        ORDER BY d.id
    """)
    entries = cursor.fetchall()
    print(f"-- ({len(entries)} rows, fixing orphaned FKs)")
    for entry in entries:
        values = [quote_value(val) for val in entry]
        print(f"INSERT INTO diary_entries (id, recipe_id, date, notes, images, dish_name, user_id, created_at, updated_at) VALUES ({', '.join(values)});")
    print("SELECT setval('diary_entries_id_seq', (SELECT COALESCE(MAX(id), 1) FROM diary_entries));")
    print()

    conn.close()

if __name__ == '__main__':
    main()
