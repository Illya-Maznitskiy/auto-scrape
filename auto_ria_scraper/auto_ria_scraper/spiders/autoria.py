import re
import os

import scrapy
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from logs.logger import logger
from auto_ria_scraper.auto_ria_scraper.helpers.odometer_extractor import (
    extract_odometer,
)
from auto_ria_scraper.auto_ria_scraper.helpers.phone_extractor import (
    extract_phone,
    clean_phone,
)
from auto_ria_scraper.auto_ria_scraper.helpers.price_extractor import (
    extract_price,
)


load_dotenv()
PAGE_TO_SCRAPE = int(os.getenv("PAGE_TO_SCRAPE", 3))


class AutoriaSpider(scrapy.Spider):
    name = "autoria"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/car/used/"]

    def __init__(self, start_page=1, end_page=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = self.get_chrome_driver(headless=False)
        self.start_page = int(start_page)
        self.end_page = int(end_page)
        self.page_counter = self.start_page
        self.start_urls = [
            f"https://auto.ria.com/car/used/?page={self.start_page}"
        ]

    def get_chrome_driver(self, headless=False):
        chrome_options = Options()

        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # ✅ Keep only essential settings for performance
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.fonts": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.javascript": 1,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )

        chrome_options.page_load_strategy = "normal"

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def parse(self, response):
        """Extract car links and follow pagination to next listing pages."""
        logger.info(
            f"Parsing listing page {self.page_counter}/{PAGE_TO_SCRAPE}: "
            f"{response.url}"
        )

        car_links = response.css("a.address::attr(href)").getall()
        for link in car_links:
            # Skip links that contain "/newauto/"
            if "/newauto/" in link:
                logger.debug(f"Skipping new car URL: {link}")
                continue

            yield response.follow(link, callback=self.parse_car)

        if self.page_counter < self.end_page:
            next_page = response.css("a.js-next::attr(href)").get()
            if next_page:
                self.page_counter += 1
                logger.info(
                    f"Following next page ({self.page_counter}): {next_page}"
                )
                yield response.follow(next_page, callback=self.parse)
        else:
            logger.info("Reached PAGE_TO_SCRAPE limit")

    def parse_car(self, response):
        """Parse car details and extract data from car page."""
        logger.info(f"[parse_car] Parsing car page: {response.url}")

        notice_text = " ".join(
            response.css("div.notice_head *::text").getall()
        ).strip()

        if re.search(r"удалено.*не принимает участия", notice_text.lower()):
            logger.info(
                f"Skipping deleted listing: {response.url} "
                f"— notice: {notice_text}"
            )
            return

        logger.info(f"[parse_car] Parsing car page: {response.url}")

        main_image_url = response.css(
            'meta[property="og:image"]::attr(content)'
        ).get(default="")

        photos_text = response.css(
            "div.action_disp_all_block a.show-all::text"
        ).get(default="")

        # Extract number from the text (e.g. "Смотреть все 62 фотографий")
        match = re.search(r"\d+", photos_text)
        images_count = int(match.group()) - 1 if match else 0

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

        if not car_vin:
            car_vin = (
                response.xpath(
                    "//span[@id='badgesVin']//span[contains(@class, "
                    "'common-text')]/text()"
                )
                .get(default="")
                .strip()
            )

        phone = extract_phone(self.driver, response.url)

        # Check if phone is a dict and contains 'main_phone'
        if isinstance(phone, dict) and "main_phone" in phone:
            raw_phone = phone["main_phone"]
        else:
            raw_phone = phone  # assume it's a string

        cleaned_phone = clean_phone(raw_phone) if raw_phone else ""

        car_data = {
            "url": response.url,
            "title": response.css("h1.head::text").get(default="").strip(),
            "price_usd": extract_price(response),
            "odometer": extract_odometer(response),
            "username": username_raw,
            "phone_number": cleaned_phone,
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
            "[parse] Parsed car_data: "
            + ", ".join(f"{k}='{v}'" for k, v in car_data.items())
        )

        yield car_data
