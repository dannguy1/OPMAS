#!/usr/bin/env python3
"""Script to run the OPMAS agent manager."""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from opmas.agents.management.manager import AgentManager
from opmas.agents.management.registry import AgentRegistry

async def main():
    """Run the agent manager."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    db_url = os.getenv("OPMAS_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/opmas")
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    
    # Create database engine and session
    engine = create_async_engine(db_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create agent registry
    registry = AgentRegistry()
    
    # Create and start agent manager
    async with async_session() as session:
        manager = AgentManager(
            db_url=db_url,
            nats_url=nats_url,
            session=session,
            registry=registry
        )
        
        try:
            await manager.start()
            print("Agent manager started. Press Ctrl+C to stop.")
            
            # Keep the manager running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping agent manager...")
        finally:
            await manager.stop()
            print("Agent manager stopped.")

if __name__ == "__main__":
    asyncio.run(main()) 