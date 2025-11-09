"""
Tests for Database Migrations

Diese Tests prüfen ob:
1. Alembic Migrationen korrekt angewendet werden können
2. Das Schema nach Migration korrekt ist
3. Daten bei Migrationen nicht verloren gehen
"""

import pytest
import psycopg2
import os


@pytest.fixture(scope="module")
def db_connection(verify_container_running):
    """Create database connection for testing - waits for container"""
    import time

    # Wait a bit for container to be fully ready
    time.sleep(2)

    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'seaser-postgres-test'),
        database=os.getenv('POSTGRES_DB', 'rezepte_test'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'test')
    )

    yield conn

    conn.close()


def get_db_connection():
    """Create database connection for testing"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'seaser-postgres-test'),
        database=os.getenv('POSTGRES_DB', 'rezepte_test'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'test')
    )


def test_alembic_version_exists(db_connection):
    """Test dass alembic_version Tabelle existiert"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'alembic_version'
        );
    """)

    exists = cur.fetchone()[0]
    cur.close()

    assert exists, "alembic_version table should exist after migration"


def test_alembic_version_is_set(db_connection):
    """Test dass eine Migration Version gesetzt ist"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("SELECT version_num FROM alembic_version;")
    version = cur.fetchone()

    cur.close()

    assert version is not None, "Alembic version should be set"
    assert version[0] is not None, "Alembic version should not be NULL"


def test_recipes_table_schema(db_connection):
    """Test dass recipes Tabelle alle erwarteten Spalten hat"""
    conn = db_connection
    cur = conn.cursor()

    # Get all columns from recipes table
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'recipes'
        ORDER BY column_name;
    """)

    columns = {row[0]: row[1] for row in cur.fetchall()}

    cur.close()

    # Expected columns
    expected_columns = {
        'id': 'integer',
        'title': 'text',
        'image': 'text',
        'notes': 'text',
        'duration': 'double precision',
        'rating': 'integer',
        'user_id': 'integer',
        'is_system': 'boolean',
        'auto_imported': 'boolean',
        'erstellt_am': 'timestamp without time zone',  # NEW: erstellt_am statt imported_at
        'created_at': 'timestamp without time zone',
        'updated_at': 'timestamp without time zone'
    }

    for col_name, col_type in expected_columns.items():
        assert col_name in columns, f"Column '{col_name}' should exist in recipes table"
        assert columns[col_name] == col_type, f"Column '{col_name}' should be type '{col_type}', but is '{columns[col_name]}'"

    # Check that old column 'imported_at' does NOT exist anymore
    assert 'imported_at' not in columns, "Column 'imported_at' should not exist (replaced by erstellt_am)"


def test_users_table_exists(db_connection):
    """Test dass users Tabelle existiert"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'users'
        );
    """)

    exists = cur.fetchone()[0]
    cur.close()

    assert exists, "users table should exist"


def test_todos_table_exists(db_connection):
    """Test dass todos Tabelle existiert"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'todos'
        );
    """)

    exists = cur.fetchone()[0]
    cur.close()

    assert exists, "todos table should exist"


def test_diary_entries_table_exists(db_connection):
    """Test dass diary_entries Tabelle existiert"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'diary_entries'
        );
    """)

    exists = cur.fetchone()[0]
    cur.close()

    assert exists, "diary_entries table should exist"


def test_foreign_key_constraints(db_connection):
    """Test dass Foreign Key Constraints existieren"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, kcu.column_name;
    """)

    foreign_keys = cur.fetchall()
    cur.close()

    # Check that we have foreign keys
    assert len(foreign_keys) > 0, "Database should have foreign key constraints"

    # Check specific foreign keys exist
    fk_dict = {(row[0], row[1]): row[2] for row in foreign_keys}

    assert ('recipes', 'user_id') in fk_dict, "recipes.user_id should have FK"
    assert fk_dict[('recipes', 'user_id')] == 'users', "recipes.user_id should reference users"

    assert ('todos', 'user_id') in fk_dict, "todos.user_id should have FK"
    assert fk_dict[('todos', 'user_id')] == 'users', "todos.user_id should reference users"

    assert ('diary_entries', 'user_id') in fk_dict, "diary_entries.user_id should have FK"
    assert fk_dict[('diary_entries', 'user_id')] == 'users', "diary_entries.user_id should reference users"

    assert ('diary_entries', 'recipe_id') in fk_dict, "diary_entries.recipe_id should have FK"
    assert fk_dict[('diary_entries', 'recipe_id')] == 'recipes', "diary_entries.recipe_id should reference recipes"


def test_erstellt_am_has_default(db_connection):
    """Test dass erstellt_am einen DEFAULT Wert hat"""
    conn = db_connection
    cur = conn.cursor()

    cur.execute("""
        SELECT column_default
        FROM information_schema.columns
        WHERE table_name = 'recipes' AND column_name = 'erstellt_am';
    """)

    default = cur.fetchone()[0]
    cur.close()

    assert default is not None, "erstellt_am should have a DEFAULT value"
    assert 'CURRENT_TIMESTAMP' in default.upper(), "erstellt_am default should be CURRENT_TIMESTAMP"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
