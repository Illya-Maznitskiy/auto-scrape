from database.connection import Database
from database.save import save_json_to_db
from logs.logger import logger


async def connect_db():
    db = Database()
    await db.connect()
    logger.info("Connected to DB.")
    return db


async def clear_old_data(db):
    await db.truncate_cars_table()
    logger.info("Old records removed from DB.")


async def save_data(db, json_file="output.json"):
    await save_json_to_db(json_file, db)
    logger.info("Data from JSON saved to DB.")


async def close_db(db):
    await db.close()
    logger.info("Database connection closed.")


async def run_db_tasks(json_file="output.json"):
    db = await connect_db()
    try:
        await clear_old_data(db)
        await save_data(db, json_file)
    finally:
        await close_db(db)
