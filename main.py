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
    process.start()  # Blocking call until crawling finishes

    logger.info("Scrapy spider finished.")


async def main():
    db = Database()
    await db.connect()  # <-- make sure this is awaited
    await save_json_to_db("output.json", db)
    await db.close()


if __name__ == "__main__":
    run_spider()  # Run outside the asyncio context

    # Now call your async database saving
    asyncio.run(main())
