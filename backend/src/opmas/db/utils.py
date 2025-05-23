# src/opmas/db_utils.py

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional
import os
from pathlib import Path

# Import Base from db_models for table creation
from .models import Base
from opmas.config import get_config

logger = logging.getLogger(__name__)

# Global engine and session factory (initialized lazily)
_engine = None
_session_factory = None
_scoped_session_factory = None

def get_db_url_from_config() -> str:
    """Constructs the database connection URL from the loaded config."""
    config = get_config()
    db_config = config.get('database')

    if not db_config:
        logger.error("Database configuration missing in opmas_config.yaml")
        raise ValueError("Database configuration is missing.")

    db_type = db_config.get('db_type')
    user = db_config.get('username')
    password = db_config.get('password')
    host = db_config.get('host')
    port = db_config.get('port')
    dbname = db_config.get('database')

    if not all([db_type, user, password, host, port, dbname]):
        logger.error("Incomplete database configuration details.")
        raise ValueError("Incomplete database configuration.")

    if db_type != "postgresql":
        logger.error(f"Unsupported database type: {db_type}. Only 'postgresql' is supported.")
        raise ValueError(f"Unsupported database type: {db_type}")

    # Construct the URL (ensure proper encoding if needed later)
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    logger.debug(f"Constructed DB URL: postgresql://{user}:***@{host}:{port}/{dbname}")
    return db_url

def get_engine():
    """Returns the SQLAlchemy engine, creating it if it doesn't exist."""
    global _engine
    if _engine is None:
        try:
            db_url = get_db_url_from_config()
            # TODO: Consider adding connection pool options (pool_size, max_overflow)
            _engine = create_engine(db_url, echo=False) # Set echo=True for SQL logging
            logger.info(f"SQLAlchemy engine created for {db_url.split('@')[-1]}")
        except ValueError as e:
            logger.critical(f"Failed to get DB configuration for engine: {e}")
            raise
        except SQLAlchemyError as e:
            logger.critical(f"Failed to create SQLAlchemy engine: {e}", exc_info=True)
            raise
    return _engine

def get_session_factory():
    """Returns the SQLAlchemy session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)
        logger.debug("SQLAlchemy session factory created.")
    return _session_factory

def get_scoped_session_factory():
    """Returns the SQLAlchemy scoped session factory for thread safety."""
    global _scoped_session_factory
    if _scoped_session_factory is None:
        engine = get_engine()
        _scoped_session_factory = scoped_session(sessionmaker(bind=engine))
        logger.debug("SQLAlchemy scoped session factory created.")
    return _scoped_session_factory

@contextmanager
def get_db_session():
    """Provide a transactional scope around a series of operations.

    Usage:
        with get_db_session() as session:
            session.add(some_object)
            session.commit()
    """
    session_factory = get_scoped_session_factory()
    session = session_factory()
    logger.debug(f"DB session {id(session)} opened.")
    try:
        yield session
        session.commit()
        logger.debug(f"DB session {id(session)} committed.")
    except SQLAlchemyError as e:
        logger.error(f"DB session {id(session)} error: {e}. Rolling back.", exc_info=True)
        session.rollback()
        raise # Re-raise the exception after rollback
    finally:
        session.close()
        logger.debug(f"DB session {id(session)} closed.")

def get_db():
    """FastAPI dependency to get a DB session."""
    session_factory = get_scoped_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close() # Ensure session is closed
        logger.debug(f"DB session {id(session)} closed (from get_db dependency).")

def init_db():
    """Initializes the database by creating all tables defined in db_models.

    This should be called once during setup or via a dedicated script.
    It is safe to call multiple times (it won't recreate existing tables).
    """
    logger.info("Initializing database...")
    try:
        engine = get_engine()
        logger.info("Creating tables based on metadata...")
        # Base.metadata contains all tables derived from Base
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully (if they didn't exist)." )
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        raise

# Optional: Function to close the engine (useful for testing or explicit shutdown)
def close_engine():
    global _engine
    if _engine:
        logger.info("Disposing SQLAlchemy engine.")
        _engine.dispose()
        _engine = None 