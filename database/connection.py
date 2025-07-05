import os

import asyncpg

from logs.logger import logger


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Establish asynchronous connection pool to the database."""
        logger.info("Connecting to database...")
        try:
            self.pool = await asyncpg.create_pool(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
            logger.info("Database connection pool created.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self):
        """Close the asynchronous database connection pool if exists."""
        if self.pool:
            logger.info("Closing database connection pool...")
            await self.pool.close()
            logger.info("Database connection pool closed.")


db = Database()
