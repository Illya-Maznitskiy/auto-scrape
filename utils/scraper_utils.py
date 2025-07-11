from multiprocessing import Process

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from auto_ria_scraper.auto_ria_scraper.spiders.autoria import AutoriaSpider
from logs.logger import logger


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

    if total_pages == 0:
        raise ValueError("No pages to scrape.")

    processes = []

    if total_pages == 1 or total_pages < chunks:
        # Run a single chunk
        start, end = 1, total_pages
        output_file = "output_chunk_1.json"

        logger.info(
            f"Launching single process to scrape pages "
            f"{start} to {end}, saving to '{output_file}'"
        )

        p = Process(target=run_spider, args=(start, end, output_file))
        p.start()
        processes.append(p)

    else:
        pages_per_chunk = total_pages // chunks
        remainder = total_pages % chunks
        logger.debug(
            f"Pages per chunk: {pages_per_chunk}, Remainder pages: {remainder}"
        )

        current_page = 1

        for i in range(chunks):
            start = current_page
            end = start + pages_per_chunk - 1
            if i < remainder:
                end += 1

            output_file = f"output_chunk_{i + 1}.json"

            logger.info(
                f"Launching process {i + 1}/{chunks} "
                f"to scrape pages {start} to {end}, saving to '{output_file}'"
            )

            p = Process(target=run_spider, args=(start, end, output_file))
            p.start()
            processes.append(p)

            current_page = end + 1

    logger.info(
        f"All {len(processes)} process(es) started, waiting for completion..."
    )

    for i, p in enumerate(processes, start=1):
        p.join()
        logger.info(f"Process {i} has finished.")

    logger.info("All parallel scraping processes have completed.")
