#!/usr/bin/env python3
"""Initialize the OPMAS database."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.append(str(src_path))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, inspect

from opmas.agents.management.models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the database."""
    try:
        # Get database URL from environment
        db_url = os.getenv("OPMAS_DB_URL", "postgresql+asyncpg://opmas:opmas@localhost:5432/opmas")
        
        # Create engine
        engine = create_async_engine(db_url)
        
        # Create tables
        async with engine.begin() as conn:
            # Check if tables exist
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables:
                logger.info("No existing tables found. Creating new tables...")
                await conn.run_sync(Base.metadata.create_all)
            else:
                logger.info(f"Found existing tables: {existing_tables}")
                # Only create tables that don't exist
                for table in Base.metadata.tables:
                    if table not in existing_tables:
                        logger.info(f"Creating table: {table}")
                        await conn.run_sync(Base.metadata.tables[table].create)
            
            # Verify agent_instances table has correct column type
            result = await conn.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'agent_instances' 
                AND column_name = 'id'
            """))
            column_type = result.scalar()
            
            if column_type != 'character varying':
                logger.info("Converting agent_instances.id column to VARCHAR")
                await conn.execute(text("""
                    ALTER TABLE agent_instances 
                    ALTER COLUMN id TYPE VARCHAR USING id::VARCHAR
                """))
        
        logger.info("Database tables verified/created successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_db()) 