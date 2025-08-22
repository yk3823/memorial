"""
Database connection and session management for Memorial Website.
Provides async SQLAlchemy setup with connection pooling and health monitoring.
"""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy import MetaData, event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine, 
    AsyncSession, 
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# SQLAlchemy metadata and base
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s", 
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

Base = declarative_base(metadata=metadata)

# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def create_database_engine(database_url: str, echo: bool = False) -> AsyncEngine:
    """
    Create async SQLAlchemy engine with optimized configuration.
    
    Args:
        database_url: PostgreSQL connection URL
        echo: Whether to echo SQL statements
        
    Returns:
        AsyncEngine: Configured database engine
    """
    settings = get_settings()
    
    # Configure connection pool based on environment
    if settings.TESTING:
        # Use NullPool for testing to avoid connection issues
        poolclass = NullPool
        pool_settings = {}
    else:
        # Use AsyncAdaptedQueuePool for production with optimized settings
        poolclass = AsyncAdaptedQueuePool
        pool_settings = {
            "pool_size": 10,  # Number of connections to maintain
            "max_overflow": 20,  # Additional connections when pool is full
            "pool_pre_ping": True,  # Validate connections before use
            "pool_recycle": 3600,  # Recycle connections every hour
        }
    
    engine = create_async_engine(
        database_url,
        echo=echo or settings.DEBUG,
        poolclass=poolclass,
        **pool_settings,
        # Additional engine options
        future=True,  # Use SQLAlchemy 2.0 style
        query_cache_size=1200,  # SQL compilation cache size
    )
    
    # Set up event listeners for connection management
    setup_engine_events(engine)
    
    global _engine
    _engine = engine
    
    logger.info(
        f"Database engine created. "
        f"Pool: {poolclass.__name__}, "
        f"Echo: {echo or settings.DEBUG}"
    )
    
    return engine


def setup_engine_events(engine: AsyncEngine) -> None:
    """Set up event listeners for database connection monitoring."""
    
    @event.listens_for(engine.sync_engine, "connect")
    def set_connection_options(dbapi_connection, connection_record):
        """Set connection-level options for each new connection."""
        # Set connection timezone to UTC
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET timezone TO 'UTC'")
        finally:
            cursor.close()
    
    @event.listens_for(engine.sync_engine, "checkout")
    def on_connection_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout events in debug mode."""
        settings = get_settings()
        if settings.DEBUG:
            logger.debug(f"Connection checked out: {connection_record}")
    
    @event.listens_for(engine.sync_engine, "checkin") 
    def on_connection_checkin(dbapi_connection, connection_record):
        """Log connection checkin events in debug mode."""
        settings = get_settings()
        if settings.DEBUG:
            logger.debug(f"Connection checked in: {connection_record}")


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create async session factory with optimized configuration.
    
    Args:
        engine: Database engine
        
    Returns:
        async_sessionmaker: Session factory
    """
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=True,  # Automatically flush before queries
        autocommit=False,  # Manual transaction control
        expire_on_commit=False,  # Keep objects accessible after commit
    )
    
    global _session_factory
    _session_factory = session_factory
    
    logger.info("Database session factory created")
    
    return session_factory


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    Yields:
        AsyncSession: Database session with automatic cleanup
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if not _session_factory:
        raise RuntimeError(
            "Database not initialized. Call create_database_engine() first."
        )
    
    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database(engine: AsyncEngine) -> None:
    """
    Initialize database schema.
    
    Args:
        engine: Database engine
    """
    logger.info("Initializing database schema...")
    
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with Base
        from app.models import (
            audit, base, memorial, permission, photo, user, psalm_119
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database schema initialized successfully")


async def check_database_health(engine: AsyncEngine) -> bool:
    """
    Check database connectivity and health.
    
    Args:
        engine: Database engine
        
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with engine.begin() as conn:
            # Simple query to test connectivity
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
        
        logger.debug("Database health check passed")
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def close_database() -> None:
    """Close database connections and cleanup resources."""
    global _engine, _session_factory
    
    if _engine:
        await _engine.dispose()
        logger.info("Database engine disposed")
        
    _engine = None
    _session_factory = None


# Database utility functions

async def execute_raw_query(query: str, params: dict = None) -> list:
    """
    Execute raw SQL query with parameters.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        list: Query results
    """
    if not _engine:
        raise RuntimeError("Database not initialized")
    
    async with _engine.begin() as conn:
        result = await conn.execute(text(query), params or {})
        return result.fetchall()


async def get_database_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database information
    """
    if not _engine:
        return {"status": "not_initialized"}
    
    try:
        async with _engine.begin() as conn:
            # Get database version
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.fetchone()[0]
            
            # Get connection count
            conn_result = await conn.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
            )
            connection_count = conn_result.fetchone()[0]
        
        return {
            "status": "connected",
            "version": version,
            "connection_count": connection_count,
            "pool_size": _engine.pool.size(),
            "checked_in": _engine.pool.checkedin(),
            "checked_out": _engine.pool.checkedout(),
            "invalid": _engine.pool.invalid(),
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e)
        }


# Context manager for database transactions

class DatabaseTransaction:
    """Context manager for database transactions with automatic rollback."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self) -> AsyncSession:
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()


async def get_transaction() -> DatabaseTransaction:
    """
    Get database transaction context manager.
    
    Returns:
        DatabaseTransaction: Transaction context manager
    """
    if not _session_factory:
        raise RuntimeError("Database not initialized")
    
    session = _session_factory()
    return DatabaseTransaction(session)