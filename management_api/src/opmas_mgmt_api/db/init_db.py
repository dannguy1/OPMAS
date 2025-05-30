"""Database initialization script."""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from opmas_mgmt_api.core.config import settings
from opmas_mgmt_api.db.base import Base
from opmas_mgmt_api.models.user import User
from opmas_mgmt_api.models.devices import Device, DeviceStatusHistory
from opmas_mgmt_api.models.agents import Agent, AgentRule, Metric
from opmas_mgmt_api.models.rules import Rule
from opmas_mgmt_api.models.findings import Finding
from opmas_mgmt_api.models.actions import Action
from opmas_mgmt_api.models.playbooks import Playbook, PlaybookExecution
from opmas_mgmt_api.models.system import SystemConfig, SystemEvent
from opmas_mgmt_api.models.configurations import Configuration, ConfigurationHistory
from opmas_mgmt_api.models.logs import LogSource, LogEntry
from opmas_mgmt_api.models.control import ControlAction
from opmas_mgmt_api.core.security import get_password_hash

logger = logging.getLogger(__name__)

def create_admin_user(session) -> None:
    """Create initial admin user if it doesn't exist."""
    try:
        # Check if admin user exists
        admin = session.get(User, settings.FIRST_SUPERUSER_ID)
        if admin is None:
            admin = User(
                id=settings.FIRST_SUPERUSER_ID,
                email=settings.FIRST_SUPERUSER_EMAIL,
                username=settings.FIRST_SUPERUSER_USERNAME,
                full_name=settings.FIRST_SUPERUSER_FULL_NAME,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                is_active=True,
                is_superuser=True
            )
            session.add(admin)
            session.commit()
            logger.info("Created initial admin user")
        else:
            logger.info("Admin user already exists")
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise

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
        
        # Drop all tables first
        Base.metadata.drop_all(bind=engine)
        logger.info("Dropped all existing tables")
        
        # Create tables in correct order
        tables = [
            User.__table__,
            Device.__table__,
            DeviceStatusHistory.__table__,
            Agent.__table__,
            AgentRule.__table__,
            Metric.__table__,
            Rule.__table__,
            Finding.__table__,
            Action.__table__,
            Playbook.__table__,
            PlaybookExecution.__table__,
            SystemConfig.__table__,
            SystemEvent.__table__,
            Configuration.__table__,
            ConfigurationHistory.__table__,
            LogSource.__table__,
            LogEntry.__table__,
            ControlAction.__table__
        ]
        
        for table in tables:
            table.create(engine)
            logger.info(f"Created table: {table.name}")
        
        # Create admin user
        Session = sessionmaker(bind=engine)
        with Session() as session:
            create_admin_user(session)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()