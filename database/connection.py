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
            await self.ensure_tables()
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self):
        if self.pool:
            logger.info("Closing database connection pool...")
            await self.pool.close()
            logger.info("Database connection pool closed.")

    async def ensure_tables(self):
        """Create tables if they don't exist."""
        create_cars_table = """
        CREATE TABLE IF NOT EXISTS cars (
            url TEXT NOT NULL,
            title TEXT,
            price_usd INTEGER,
            odometer INTEGER,
            username TEXT,
            phone_number TEXT,
            image_url TEXT,
            images_count INTEGER,
            car_number TEXT,
            car_vin TEXT PRIMARY KEY,
            datetime_found TIMESTAMP
        );
        """
        try:
            async with self.pool.acquire() as conn:
                logger.info("Checking and creating 'cars' table if needed...")
                await conn.execute(create_cars_table)
                logger.info("Table 'cars' created or already exists.")
        except Exception as e:
            logger.error(f"Error creating 'cars' table: {e}")
            raise

    async def truncate_cars_table(self):
        """Clear all existing data in the cars table."""
        try:
            async with self.pool.acquire() as conn:
                logger.info("Cleaning 'cars' table...")
                await conn.execute("TRUNCATE TABLE cars;")
                logger.info("'cars' table cleaned successfully.")
        except Exception as e:
            logger.error(f"Error cleaning 'cars' table: {e}")
            raise


db = Database()
