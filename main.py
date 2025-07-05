import io
import json

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from auto_ria_scraper.auto_ria_scraper.spiders.autoria import AutoriaSpider
from logs.logger import logger


def main():
    """Start Scrapy crawler and save results to a JSON file."""
    logger.info("Starting crawler via main()")

    settings = get_project_settings()
    settings.set(
        "FEEDS",
        {
            "output.json": {
                "format": "json",
                "overwrite": True,
                "encoding": "utf-8",
            },
        },
    )

    process = CrawlerProcess(settings)
    process.crawl(AutoriaSpider)
    process.start()

    logger.info("Crawling completed.")


if __name__ == "__main__":
    main()
