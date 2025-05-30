import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.core.security import get_password_hash
from opmas_mgmt_api.db.base_class import Base
from opmas_mgmt_api.models.user import User
from opmas_mgmt_api.models.devices import Device
from opmas_mgmt_api.models.agents import Agent
from opmas_mgmt_api.models.rules import Rule
from opmas_mgmt_api.models.actions import Action
from opmas_mgmt_api.models.findings import Finding
from opmas_mgmt_api.models.system import SystemConfig, SystemEvent
from opmas_mgmt_api.models.configurations import Configuration, ConfigurationHistory
from opmas_mgmt_api.models.logs import LogSource, LogEntry
from opmas_mgmt_api.models.control import ControlAction
from opmas_mgmt_api.models.playbooks import Playbook, PlaybookExecution

logger = logging.getLogger(__name__)

def init_db() -> None:
    """Initialize the database."""
    try:
        # Create engine
        engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT
        )
        
        # Drop all tables with CASCADE
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()
        logger.info("Dropped all existing tables")
        
        # Create tables in correct order
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Create admin user
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            # Check if admin user exists
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("admin123"),
                    full_name="System Administrator",
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin_user)
                db.commit()
                logger.info("Created admin user successfully")
            else:
                logger.info("Admin user already exists")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()