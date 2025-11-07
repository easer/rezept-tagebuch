#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
Simple direct copy without ORM complexity
"""

import sqlite3
import psycopg2
import os
import sys
from datetime import datetime

def connect_sqlite(db_path):
    """Connect to SQLite database"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def connect_postgres():
    """Connect to PostgreSQL database"""
    host = os.environ.get('POSTGRES_HOST', '10.89.0.28')
    port = os.environ.get('POSTGRES_PORT', '5432')
    database = os.environ.get('POSTGRES_DB', 'rezepte')
    user = os.environ.get('POSTGRES_USER', 'postgres')
    password = os.environ.get('POSTGRES_PASSWORD', 'seaser')

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    return conn

def migrate_users(sqlite_conn, pg_conn):
    """Migrate users table"""
    print("Migrating users...")

    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT * FROM users ORDER BY id")
    users = sqlite_cur.fetchall()

    pg_cur = pg_conn.cursor()

    for user in users:
        pg_cur.execute("""
            INSERT INTO users (id, email, name, avatar_color, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, (user['id'], user['email'], user['name'],
              user['avatar_color'], user['created_at']))

    # Update sequence
    pg_cur.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")

    pg_conn.commit()
    print(f"✓ Migrated {len(users)} users")

def migrate_recipes(sqlite_conn, pg_conn):
    """Migrate recipes table"""
    print("Migrating recipes...")

    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT * FROM recipes ORDER BY id")
    recipes = sqlite_cur.fetchall()

    pg_cur = pg_conn.cursor()

    for recipe in recipes:
        pg_cur.execute("""
            INSERT INTO recipes (
                id, title, image, notes, duration, rating,
                user_id, is_system, auto_imported, imported_at,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            recipe['id'], recipe['title'], recipe['image'],
            recipe['notes'], recipe['duration'], recipe['rating'],
            recipe['user_id'], recipe['is_system'],
            recipe['auto_imported'], recipe['imported_at'],
            recipe['created_at'], recipe['updated_at']
        ))

    # Update sequence
    pg_cur.execute("SELECT setval('recipes_id_seq', (SELECT MAX(id) FROM recipes))")

    pg_conn.commit()
    print(f"✓ Migrated {len(recipes)} recipes")

def migrate_todos(sqlite_conn, pg_conn):
    """Migrate todos table"""
    print("Migrating todos...")

    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT * FROM todos ORDER BY id")
    todos = sqlite_cur.fetchall()

    pg_cur = pg_conn.cursor()

    for todo in todos:
        pg_cur.execute("""
            INSERT INTO todos (
                id, text, priority, completed, user_id,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            todo['id'], todo['text'], todo['priority'],
            todo['completed'], todo['user_id'],
            todo['created_at'], todo['updated_at']
        ))

    # Update sequence
    pg_cur.execute("SELECT setval('todos_id_seq', (SELECT MAX(id) FROM todos))")

    pg_conn.commit()
    print(f"✓ Migrated {len(todos)} todos")

def migrate_diary_entries(sqlite_conn, pg_conn):
    """Migrate diary_entries table"""
    print("Migrating diary entries...")

    sqlite_cur = sqlite_conn.cursor()
    sqlite_cur.execute("SELECT * FROM diary_entries ORDER BY id")
    entries = sqlite_cur.fetchall()

    pg_cur = pg_conn.cursor()

    for entry in entries:
        pg_cur.execute("""
            INSERT INTO diary_entries (
                id, recipe_id, date, notes, images, dish_name,
                user_id, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            entry['id'], entry['recipe_id'], entry['date'],
            entry['notes'], entry['images'], entry['dish_name'],
            entry['user_id'], entry['created_at'], entry['updated_at']
        ))

    # Update sequence
    pg_cur.execute("SELECT setval('diary_entries_id_seq', (SELECT MAX(id) FROM diary_entries))")

    pg_conn.commit()
    print(f"✓ Migrated {len(entries)} diary entries")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 migrate-data-to-postgres.py <sqlite_db_path>")
        print("Example: python3 migrate-data-to-postgres.py data/prod/rezepte.db")
        sys.exit(1)

    sqlite_db_path = sys.argv[1]

    if not os.path.exists(sqlite_db_path):
        print(f"Error: SQLite database not found: {sqlite_db_path}")
        sys.exit(1)

    print(f"Starting migration from {sqlite_db_path} to PostgreSQL...")
    print()

    # Connect to databases
    sqlite_conn = connect_sqlite(sqlite_db_path)
    pg_conn = connect_postgres()

    try:
        # Migrate in order (respecting foreign keys)
        migrate_users(sqlite_conn, pg_conn)
        migrate_recipes(sqlite_conn, pg_conn)
        migrate_todos(sqlite_conn, pg_conn)
        migrate_diary_entries(sqlite_conn, pg_conn)

        print()
        print("✓ Migration completed successfully!")

        # Show stats
        pg_cur = pg_conn.cursor()
        pg_cur.execute("SELECT COUNT(*) FROM users")
        user_count = pg_cur.fetchone()[0]
        pg_cur.execute("SELECT COUNT(*) FROM recipes")
        recipe_count = pg_cur.fetchone()[0]
        pg_cur.execute("SELECT COUNT(*) FROM todos")
        todo_count = pg_cur.fetchone()[0]
        pg_cur.execute("SELECT COUNT(*) FROM diary_entries")
        diary_count = pg_cur.fetchone()[0]

        print()
        print("PostgreSQL database stats:")
        print(f"  Users: {user_count}")
        print(f"  Recipes: {recipe_count}")
        print(f"  Todos: {todo_count}")
        print(f"  Diary Entries: {diary_count}")

    except Exception as e:
        print(f"Error during migration: {e}")
        pg_conn.rollback()
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == '__main__':
    main()
