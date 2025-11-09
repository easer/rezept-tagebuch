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
    """Get database URL from config file or environment variable"""
    # Priority: alembic.ini config > environment variable
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url

    # Fallback to SQLite for backward compatibility
    db_path = os.getenv('DB_PATH', '/data/rezepte.db')
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
