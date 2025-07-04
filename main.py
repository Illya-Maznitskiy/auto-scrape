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
            },
        },
    )

    process = CrawlerProcess(settings)
    process.crawl(AutoriaSpider)
    process.start()

    logger.info("Crawling completed.")

    with open("output.json", "r", encoding="utf-8") as infile:
        data = json.load(infile)

    with open("output_result.json", "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=2)

    logger.info("Final JSON saved with Cyrillic preserved.")


if __name__ == "__main__":
    main()
