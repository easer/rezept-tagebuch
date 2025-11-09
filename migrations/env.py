"""Alembic Environment Configuration for Rezept-Tagebuch"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata (we'll define this manually since we use raw SQL)
target_metadata = None

def get_url():
    """Get database URL based on environment (DEV/TEST/PROD)"""
    # Check for environment-based configuration
    DB_TYPE = os.environ.get('DB_TYPE', 'postgresql')
    TESTING_MODE = os.environ.get('TESTING_MODE', 'false').lower() == 'true'
    DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'

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
            # Production database (fallback to alembic.ini if env vars not set)
            url = config.get_main_option("sqlalchemy.url")
            if url:
                return url
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

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_url()

    # Determine if we need batch mode (only for SQLite)
    render_as_batch = url.startswith('sqlite:///')

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=render_as_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    url = get_url()
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Determine if we need batch mode (only for SQLite)
    render_as_batch = url.startswith('sqlite:///')

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=render_as_batch,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
