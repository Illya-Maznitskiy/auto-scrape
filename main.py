import asyncio
import glob
import json
import os
from multiprocessing import Process

from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from database.connection import Database
from logs.logger import logger
from auto_ria_scraper.auto_ria_scraper.spiders.autoria import AutoriaSpider
from database.save import save_json_to_db
from database.backup_db import create_backup


load_dotenv()

JSON_OUTPUT_FILE = "output.json"
PAGE_TO_SCRAPE = int(os.getenv("PAGE_TO_SCRAPE", 3))
CHUNKS = int(os.getenv("CHUNKS", 3))  # default to 3 if missing


def run_spider(start_page, end_page, output_file):
    logger.info(f"Running spider for pages {start_page} to {end_page}...")

    settings = get_project_settings()
    settings.set(
        "FEEDS",
        {
            output_file: {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
            },
        },
    )

    process = CrawlerProcess(settings)
    process.crawl(AutoriaSpider, start_page=start_page, end_page=end_page)
    process.start()


def run_parallel_spiders(total_pages=3, chunks=3):
    logger.info(
        f"Starting parallel scraping: "
        f"total_pages={total_pages}, chunks={chunks}"
    )

    pages_per_chunk = total_pages // chunks
    remainder = total_pages % chunks
    logger.debug(
        f"Pages per chunk: {pages_per_chunk}, Remainder pages: {remainder}"
    )

    processes = []

    for i in range(chunks):
        start = i * pages_per_chunk + 1
        # Add remainder pages to the last chunk
        end = (i + 1) * pages_per_chunk
        if i == chunks - 1:
            end += remainder

        output_file = f"output_chunk_{i + 1}.json"

        logger.info(
            f"Launching process {i + 1}/{chunks} "
            f"to scrape pages {start} to {end}, saving to '{output_file}'"
        )

        p = Process(target=run_spider, args=(start, end, output_file))
        p.start()
        processes.append(p)

    logger.info(f"All {chunks} processes started, waiting for completion...")

    for i, p in enumerate(processes, start=1):
        p.join()
        logger.info(f"Process {i} has finished.")

    logger.info("All parallel scraping processes have completed.")


def merge_output_chunks(
    output_pattern="output_chunk_*.json", merged_file="output.json"
):
    logger.info(
        f"Merging chunk files matching '{output_pattern}' into '{merged_file}'"
    )

    merged_data = []

    for file_name in sorted(glob.glob(output_pattern)):
        logger.info(f"Reading from {file_name}")
        with open(file_name, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    logger.warning(f"{file_name} did not contain a list")
            except json.JSONDecodeError as e:
                logger.error(f"Could not decode JSON from {file_name}: {e}")

    with open(merged_file, "w", encoding="utf-8") as out_file:
        json.dump(merged_data, out_file, ensure_ascii=False, indent=2)

    logger.info(f"Merged {len(merged_data)} records into '{merged_file}'")


def cleanup_old_chunks(pattern="output_chunk_*.json"):
    for file_path in glob.glob(pattern):
        try:
            os.remove(file_path)
            logger.info(f"Deleted old chunk file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")


async def main():
    """Connect to DB, clean old data, save JSON, close connection."""
    logger.info("Starting main execution...")
    db = Database()

    await db.connect()
    logger.info("Connected to DB.")

    await db.truncate_cars_table()
    logger.info("Old records removed from DB.")

    await save_json_to_db("output.json", db)
    logger.info("Data from JSON saved to DB.")

    await db.close()
    logger.info("Database connection closed.")

    create_backup()


if __name__ == "__main__":
    # Delete old chunk files to avoid merging stale data
    cleanup_old_chunks()

    # Run scrapers
    run_parallel_spiders(total_pages=PAGE_TO_SCRAPE, chunks=CHUNKS)

    # Merge all new chunks into one file
    merge_output_chunks()

    # Process and backup
    asyncio.run(main())
