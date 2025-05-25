import os
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from .test_config import TestConfig


class TestDatabase:
    def __init__(self, config: Optional[TestConfig] = None):
        self.config = config or TestConfig()
        self.conn = None
        self.schema_file = Path(__file__).parent.parent / "fixtures" / "schemas" / "test_schema.sql"

    def connect(self):
        """Connect to the test database."""
        db_config = self.config.database_config
        self.conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["name"],
        )
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return self.conn

    def create_database(self):
        """Create test database if it doesn't exist."""
        db_config = self.config.database_config
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_config['name']}'")
            exists = cur.fetchone()
            if not exists:
                cur.execute(f"CREATE DATABASE {db_config['name']}")

        conn.close()

    def initialize_schema(self):
        """Initialize database schema from SQL file."""
        if not self.conn:
            self.connect()

        with open(self.schema_file, "r") as f:
            schema_sql = f.read()

        with self.conn.cursor() as cur:
            cur.execute(schema_sql)

    def cleanup(self):
        """Clean up test database."""
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    DROP TABLE IF EXISTS logs CASCADE;
                    DROP TABLE IF EXISTS rules CASCADE;
                    DROP TABLE IF EXISTS devices CASCADE;
                """
                )
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.create_database()
        self.connect()
        self.initialize_schema()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
