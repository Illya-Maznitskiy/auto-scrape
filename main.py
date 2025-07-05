import asyncio
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from database.connection import Database
from logs.logger import logger
from auto_ria_scraper.auto_ria_scraper.spiders.autoria import AutoriaSpider
from database.save import save_json_to_db


load_dotenv()

JSON_OUTPUT_FILE = "output.json"


def run_spider():
    """Configure and run Scrapy spider, saving results to JSON."""
    logger.info("Starting Scrapy spider...")

    settings = get_project_settings()
    settings.set(
        "FEEDS",
        {
            JSON_OUTPUT_FILE: {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
            },
        },
    )

    process = CrawlerProcess(settings)
    process.crawl(AutoriaSpider)
    process.start()

    logger.info("Scrapy spider finished.")


async def main():
    """Connect to DB, save JSON data, then close connection."""
    logger.info("Starting main execution...")
    db = Database()

    await db.connect()
    logger.info("Connected to DB.")

    await save_json_to_db("output.json", db)
    logger.info("Data from JSON saved to DB.")

    await db.close()
    logger.info("Database connection closed.")


if __name__ == "__main__":
    run_spider()

    asyncio.run(main())
