import re
import scrapy

from logs.logger import logger
from auto_ria_scraper.auto_ria_scraper.helpers.selenium_helper import (
    get_chrome_driver,
)
from auto_ria_scraper.auto_ria_scraper.helpers.extractors import (
    extract_price,
    extract_odometer,
    extract_phone,
    clean_phone,
)


class AutoriaSpider(scrapy.Spider):
    name = "autoria"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/car/used/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = get_chrome_driver(headless=False)

    def parse(self, response):
        """Extract car links and follow pagination to next listing pages."""
        logger.info(f"Parsing listing page: {response.url}")

        car_links = response.css("a.address::attr(href)").getall()
        for link in car_links:
            yield response.follow(link, callback=self.parse_car)

        next_page = response.css("a.js-next::attr(href)").get()
        if next_page:
            logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)
        else:
            logger.info("No next page found")

    def parse_car(self, response):
        """Parse car details and extract data from car page."""
        logger.info(f"[parse_car] Parsing car page: {response.url}")

        main_image_url = response.css(
            'meta[property="og:image"]::attr(content)'
        ).get(default="")

        photos_text = response.css(
            "div.action_disp_all_block a.show-all::text"
        ).get(default="")

        # Extract number from the text (e.g. "Смотреть все 62 фотографий")
        match = re.search(r"\d+", photos_text)
        images_count = int(match.group()) if match else 0

        username_raw = (
            response.css("div.seller_info_name a::text").get()
            or response.css("div.seller_info_name::text").get()
            or response.css("h4.seller_info_name a::text").get()
            or ""
        ).strip()
        car_number = (
            response.xpath("//span[contains(@class,'state-num')]/text()")
            .get(default="")
            .strip()
        )
        car_vin = (
            response.xpath("//span[contains(@class, 'label-vin')]/text()")
            .get(default="")
            .strip()
        )
        car_data = {
            "url": response.url,
            "title": response.css("h1.head::text").get(),
            "price_usd": extract_price(response),
            "odometer": extract_odometer(response),
            "username": username_raw,
            "phone_number": clean_phone(
                extract_phone(self.driver, response.url)
            ),
            "image_url": main_image_url,
            "images_count": images_count,
            "car_number": car_number,
            "car_vin": car_vin,
            "datetime_found": (
                response.headers.get("Date").decode("utf-8")
                if response.headers.get("Date")
                else None
            ),
        }

        logger.info(
            "[parse_car] Parsed car_data: "
            + ", ".join(f"{k}='{v}'" for k, v in car_data.items())
        )

        yield car_data
