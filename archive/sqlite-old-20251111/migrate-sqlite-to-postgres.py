#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL
Reads from SQLite database and writes to PostgreSQL using SQLAlchemy models
"""
import sys
import os
import sqlite3
from datetime import datetime, date

# Add parent directory to path to import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask
from models import db, User, Recipe, Todo, DiaryEntry
from config import SQLALCHEMY_DATABASE_URI, UPLOAD_FOLDER

def migrate_data(sqlite_db_path, target_env='prod'):
    """
    Migrate data from SQLite to PostgreSQL

    Args:
        sqlite_db_path: Path to SQLite database file
        target_env: Target environment ('prod' or 'test')
    """
    print(f"🔄 Starting migration from SQLite to PostgreSQL")
    print(f"   Source: {sqlite_db_path}")
    print(f"   Target: {SQLALCHEMY_DATABASE_URI}")
    print()

    # Initialize Flask app for SQLAlchemy context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Create all tables in PostgreSQL
        print("📦 Creating tables in PostgreSQL...")
        db.create_all()
        print("   ✅ Tables created")
        print()

        # Connect to SQLite
        print(f"📂 Reading data from SQLite: {sqlite_db_path}")
        conn = sqlite3.connect(sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Migrate Users
        print("👥 Migrating users...")
        cursor.execute("SELECT * FROM users ORDER BY id")
        users_data = cursor.fetchall()
        user_count = 0
        for row in users_data:
            user = User(
                id=row['id'],
                email=row['email'],
                name=row['name'],
                avatar_color=row['avatar_color'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow()
            )
            db.session.add(user)
            user_count += 1
        db.session.commit()
        print(f"   ✅ Migrated {user_count} users")

        # Migrate Recipes
        print("📖 Migrating recipes...")
        cursor.execute("SELECT * FROM recipes ORDER BY id")
        recipes_data = cursor.fetchall()
        recipe_count = 0
        for row in recipes_data:
            recipe = Recipe(
                id=row['id'],
                title=row['title'],
                image=row['image'],
                notes=row['notes'],
                duration=row['duration'],
                rating=row['rating'],
                user_id=row['user_id'],
                is_system=bool(row['is_system']) if row['is_system'] is not None else False,
                auto_imported=bool(row['auto_imported']) if row['auto_imported'] is not None else False,
                imported_at=date.fromisoformat(row['imported_at']) if row['imported_at'] else None,
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            db.session.add(recipe)
            recipe_count += 1
        db.session.commit()
        print(f"   ✅ Migrated {recipe_count} recipes")

        # Migrate Todos
        print("✅ Migrating todos...")
        cursor.execute("SELECT * FROM todos ORDER BY id")
        todos_data = cursor.fetchall()
        todo_count = 0
        for row in todos_data:
            todo = Todo(
                id=row['id'],
                text=row['text'],
                priority=row['priority'],
                completed=bool(row['completed']) if row['completed'] is not None else False,
                user_id=row['user_id'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            db.session.add(todo)
            todo_count += 1
        db.session.commit()
        print(f"   ✅ Migrated {todo_count} todos")

        # Migrate Diary Entries
        print("📔 Migrating diary entries...")
        cursor.execute("SELECT * FROM diary_entries ORDER BY id")
        diary_data = cursor.fetchall()
        diary_count = 0
        for row in diary_data:
            entry = DiaryEntry(
                id=row['id'],
                recipe_id=row['recipe_id'],
                dish_name=row['dish_name'] if 'dish_name' in row.keys() else None,
                date=date.fromisoformat(row['date']) if row['date'] else date.today(),
                notes=row['notes'],
                images=row['images'],
                user_id=row['user_id'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else datetime.utcnow()
            )
            db.session.add(entry)
            diary_count += 1
        db.session.commit()
        print(f"   ✅ Migrated {diary_count} diary entries")

        conn.close()

        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ Migration completed successfully!")
        print(f"   Users: {user_count}")
        print(f"   Recipes: {recipe_count}")
        print(f"   Todos: {todo_count}")
        print(f"   Diary Entries: {diary_count}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print()
        print("⚠️  Remember to copy uploads folder:")
        print(f"   cp -r data/prod/uploads/* data/postgres-uploads/")
        print()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate data from SQLite to PostgreSQL')
    parser.add_argument('sqlite_db_path', help='Path to SQLite database file')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    sqlite_path = args.sqlite_db_path

    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        sys.exit(1)

    # Confirm migration
    if not args.yes:
        print("⚠️  WARNING: This will migrate data to PostgreSQL")
        print(f"   Source: {sqlite_path}")
        print(f"   Target: {os.environ.get('POSTGRES_HOST', 'seaser-postgres')}")
        print()
        response = input("Continue? [y/N]: ")

        if response.lower() != 'y':
            print("Migration cancelled.")
            sys.exit(0)

    migrate_data(sqlite_path)
