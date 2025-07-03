from scrapy.crawler import CrawlerProcess

from auto_ria_scraper.auto_ria_scraper.spiders.autoria import AutoriaSpider
from logs.logger import logger


def main():
    """Start Scrapy crawler and save results to a JSON file."""
    logger.info("Initializing crawler process...")

    process = CrawlerProcess(
        settings={
            "FEEDS": {
                "results.json": {"format": "json"},
            },
            "LOG_LEVEL": "INFO",
        }
    )

    logger.info("Starting AutoriaSpider...")
    process.crawl(AutoriaSpider)
    process.start()

    logger.info("Crawling completed. Results saved to 'results.json'.")


if __name__ == "__main__":
    main()
