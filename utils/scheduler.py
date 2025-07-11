import os
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from logs.logger import logger
from main import main as run_workflow  # import your scraping workflow function
from database.backup_db import create_backup


load_dotenv()

SCRAPER_RUN_TIME = os.getenv("SCRAPER_RUN_TIME", "12:00")
DUMP_RUN_TIME = os.getenv(
    "DUMP_RUN_TIME", "12:30"
)  # example: different time for dump


async def backup_task():
    logger.info("Starting DB backup task")
    loop = asyncio.get_event_loop()
    # Run the blocking create_backup() in a thread to not block the event loop
    await loop.run_in_executor(None, create_backup)
    logger.info("DB backup task finished")


def parse_time(t):
    hour, minute = map(int, t.split(":"))
    return hour, minute


async def schedule_tasks():
    scheduler = AsyncIOScheduler()

    h_scrape, m_scrape = parse_time(SCRAPER_RUN_TIME)
    h_dump, m_dump = parse_time(DUMP_RUN_TIME)

    # Schedule run_workflow coroutine directly
    scheduler.add_job(run_workflow, "cron", hour=h_scrape, minute=m_scrape)

    # Schedule backup_task coroutine directly
    scheduler.add_job(backup_task, "cron", hour=h_dump, minute=m_dump)

    scheduler.start()
    logger.info(
        f"Scheduler started with scraping at {SCRAPER_RUN_TIME} and backup at {DUMP_RUN_TIME}"
    )

    try:
        await asyncio.Event().wait()  # keeps running forever
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(schedule_tasks())
