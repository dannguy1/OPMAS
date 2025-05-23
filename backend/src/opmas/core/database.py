from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .config import ConfigManager, DatabaseConfig
from .models import Base

class DatabaseManager:
    """Manage database connections and sessions."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or ConfigManager().get_config().database
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling."""
        return create_engine(
            f"postgresql://{self.config.user}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}",
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_db(self) -> None:
        """Initialize database tables."""
        Base.metadata.create_all(bind=self.engine)

    def drop_db(self) -> None:
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine) 