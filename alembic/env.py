"""
Alembic environment configuration for Memorial Website.
Handles database migrations with async SQLAlchemy support.
"""

import asyncio
import logging
from logging.config import fileConfig
from typing import Any

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import models and database configuration
from app.core.config import get_settings
from app.models import Base  # This imports all models

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()
database_url = settings.DATABASE_URL

# Override database URL in alembic config
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is also acceptable here. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with database connection.
    
    Args:
        connection: Database connection
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        # Render item for autogenerate support
        render_as_batch=False,
        # Include object naming conventions
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object: Any, name: str, type_: str, reflected: bool, compare_to: Any) -> bool:
    """
    Determine whether to include an object in migrations.
    
    Args:
        object: SQLAlchemy object
        name: Object name
        type_: Object type (table, column, etc.)
        reflected: Whether object was reflected from database
        compare_to: Object to compare to
        
    Returns:
        bool: True if object should be included
    """
    # Skip tables that don't belong to our application
    if type_ == "table":
        # Skip system tables
        if name.startswith("pg_") or name.startswith("information_schema"):
            return False
        
        # Skip alembic version table
        if name == "alembic_version":
            return False
    
    return True


async def run_async_migrations() -> None:
    """Run migrations asynchronously."""
    # Create async engine for migrations
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
        echo=settings.DEBUG,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    # Run async migrations
    asyncio.run(run_async_migrations())


# Determine which mode to run in
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()