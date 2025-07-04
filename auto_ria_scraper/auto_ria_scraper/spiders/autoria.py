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
        logger.info(f"[parse_car] Parsing car page: {response.url}")

        main_image_url = response.css(
            'meta[property="og:image"]::attr(content)'
        ).get()

        # Extract images count text from the 'show-all' link
        photos_text = response.css(
            "div.action_disp_all_block a.show-all::text"
        ).get(default="")

        # Extract number from the text (e.g. "Смотреть все 62 фотографий")
        import re

        match = re.search(r"\d+", photos_text)
        images_count = int(match.group()) if match else 0

        username_raw = (
            response.css("div.seller_info_name::text").get(default="").strip()
        )

        logger.debug(f"[parse_car] Found {images_count} image(s)")
        logger.debug(f"[parse_car] Extracted username: '{username_raw}'")

        car_number = response.xpath(
            "//span[contains(@class,'state-num')]/text()"
        ).get()
        car_vin = response.xpath(
            "//span[contains(@class, 'label-vin')]/text()"
        ).get()

        if not username_raw:
            logger.warning(
                f"[parse_car] Username not found on page: {response.url}"
            )
        if not car_vin:
            logger.warning(
                f"[parse_car] VIN not found on page: {response.url}"
            )

        yield {
            "url": response.url,
            "title": response.css("h1.head::text").get(),
            "price_usd": extract_price(response),
            "odometer": extract_odometer(response),
            "username": username_raw,
            "phone_number": extract_phone(self.driver, response.url),
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
