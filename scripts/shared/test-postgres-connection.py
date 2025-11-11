#!/usr/bin/env python3
"""
Test PostgreSQL connection and basic ORM operations
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask
from config import SQLALCHEMY_DATABASE_URI, DB_TYPE
from models import db, User, Recipe, Todo, DiaryEntry

def test_connection():
    """Test database connection"""
    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    print()

    print(f"Database Type: {DB_TYPE}")
    print(f"Database URL: {SQLALCHEMY_DATABASE_URI}")
    print()

    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db
    db.init_app(app)

    with app.app_context():
        try:
            # Test connection
            print("Testing database connection...")
            db.session.execute(db.text('SELECT 1'))
            print("✓ Connection successful!")
            print()

            # Test table access
            print("Testing table access...")

            # Users
            users = User.query.all()
            print(f"✓ Users table: {len(users)} users")
            if users:
                print(f"  Example: {users[0].name} ({users[0].email})")

            # Recipes
            recipes = Recipe.query.all()
            print(f"✓ Recipes table: {len(recipes)} recipes")
            if recipes:
                print(f"  Example: {recipes[0].title}")

            # Todos
            todos = Todo.query.all()
            print(f"✓ Todos table: {len(todos)} todos")
            if todos:
                print(f"  Example: {todos[0].text}")

            # Diary Entries
            entries = DiaryEntry.query.all()
            print(f"✓ Diary Entries table: {len(entries)} entries")
            if entries:
                print(f"  Example: {entries[0].dish_name} on {entries[0].date}")

            print()
            print("=" * 60)
            print("✅ All tests passed!")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
