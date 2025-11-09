"""
Database Configuration for Rezept-Tagebuch
Supports both SQLite (legacy) and PostgreSQL
"""
import os

# Database Configuration
# Default to PostgreSQL, fallback to SQLite for backwards compatibility
DB_TYPE = os.environ.get('DB_TYPE', 'postgresql')  # 'postgresql' or 'sqlite'
TESTING_MODE = os.environ.get('TESTING_MODE', 'false').lower() == 'true'
DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'

def get_database_url():
    """
    Returns the appropriate database URL based on environment

    PostgreSQL URL format:
    postgresql://user:password@host:port/database

    SQLite URL format:
    sqlite:////absolute/path/to/database.db
    """
    if DB_TYPE == 'postgresql':
        # PostgreSQL Configuration
        if TESTING_MODE:
            # Test database
            pg_host = os.environ.get('POSTGRES_TEST_HOST', 'seaser-postgres-test')
            pg_port = os.environ.get('POSTGRES_TEST_PORT', '5432')
            pg_db = os.environ.get('POSTGRES_TEST_DB', 'rezepte_test')
            pg_user = os.environ.get('POSTGRES_TEST_USER', 'postgres')
            pg_password = os.environ.get('POSTGRES_TEST_PASSWORD', 'test')
        elif DEV_MODE:
            # Development database
            pg_host = os.environ.get('POSTGRES_DEV_HOST', 'seaser-postgres-dev')
            pg_port = os.environ.get('POSTGRES_DEV_PORT', '5432')
            pg_db = os.environ.get('POSTGRES_DEV_DB', 'rezepte_dev')
            pg_user = os.environ.get('POSTGRES_DEV_USER', 'postgres')
            pg_password = os.environ.get('POSTGRES_DEV_PASSWORD', 'seaser')
        else:
            # Production database
            pg_host = os.environ.get('POSTGRES_HOST', 'seaser-postgres')
            pg_port = os.environ.get('POSTGRES_PORT', '5432')
            pg_db = os.environ.get('POSTGRES_DB', 'rezepte')
            pg_user = os.environ.get('POSTGRES_USER', 'postgres')
            pg_password = os.environ.get('POSTGRES_PASSWORD', 'seaser')

        return f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}'

    else:
        # SQLite Configuration (legacy fallback)
        if TESTING_MODE:
            db_path = '/data/test/rezepte.db'
        else:
            db_path = '/data/rezepte.db'

        return f'sqlite:///{db_path}'


# SQLAlchemy Configuration
SQLALCHEMY_DATABASE_URI = get_database_url()
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 300,    # Recycle connections after 5 minutes
}

# Upload Folder Configuration
if TESTING_MODE:
    UPLOAD_FOLDER = '/data/test/uploads'
elif DEV_MODE:
    UPLOAD_FOLDER = '/data/dev/uploads'
else:
    UPLOAD_FOLDER = '/data/uploads'

# Print config on startup
if __name__ == '__main__':
    print(f"Database Type: {DB_TYPE}")
    print(f"Testing Mode: {TESTING_MODE}")
    print(f"Dev Mode: {DEV_MODE}")
    print(f"Database URL: {SQLALCHEMY_DATABASE_URI}")
    print(f"Upload Folder: {UPLOAD_FOLDER}")
