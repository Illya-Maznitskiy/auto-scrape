import scrapy
from logs.logger import logger
from auto_ria_scraper.auto_ria_scraper.helpers.selenium_helper import (
    get_chrome_driver,
)
from auto_ria_scraper.auto_ria_scraper.helpers.extractors import (
    extract_price,
    extract_odometer,
    extract_phone,
)


class AutoriaSpider(scrapy.Spider):
    name = "autoria"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/car/used/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = get_chrome_driver(headless=False)

    def parse(self, response):
        logger.info(f"Parsing listing page: {response.url}")
        car_links = response.css("a.address::attr(href)").getall()
        for link in car_links:
            yield response.follow(link, callback=self.parse_car)

        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_car(self, response):
        logger.info(f"Parsing car page: {response.url}")
        images = response.css("div.gallery img::attr(src)").getall()
        yield {
            "url": response.url,
            "title": response.css("h1.head::text").get(),
            "price_usd": extract_price(response),
            "odometer": extract_odometer(response),
            "username": response.css("div.seller_info_name span::text").get(),
            "phone_number": extract_phone(self.driver, response.url),
            "image_url": images[0] if images else None,
            "images_count": len(images),
            "car_number": response.xpath(
                "//span[contains(@class,'state-num')]/text()"
            ).get(),
            "car_vin": response.xpath(
                "//span[contains(@class, 'label-vin')]/text()"
            ).get(),
            "datetime_found": (
                response.headers.get("Date").decode("utf-8")
                if response.headers.get("Date")
                else None
            ),
        }
