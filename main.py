import asyncio
import os

from dotenv import load_dotenv

from logs.logger import logger
from database.db_utils import run_db_tasks
from utils.file_utils import cleanup_old_chunks, merge_output_chunks
from utils.scraper_utils import run_parallel_spiders


load_dotenv()

PAGE_TO_SCRAPE = int(os.getenv("PAGE_TO_SCRAPE", 3))
CHUNKS = int(os.getenv("CHUNKS", 3))


async def main():
    logger.info("Starting full scraping workflow")

    logger.info("Cleaning up old chunk files")
    # Delete old chunk files to avoid merging stale data
    cleanup_old_chunks()

    logger.info(
        f"Running spiders for {PAGE_TO_SCRAPE} pages in {CHUNKS} chunks"
    )
    run_parallel_spiders(total_pages=PAGE_TO_SCRAPE, chunks=CHUNKS)

    logger.info("Merging output chunk files")
    merge_output_chunks()

    logger.info("Running DB tasks (save and backup)")
    await run_db_tasks()

    logger.info("Workflow complete")


if __name__ == "__main__":
    asyncio.run(main())
