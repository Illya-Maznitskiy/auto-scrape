import scrapy

from logs.logger import logger


class AutoriaSpider(scrapy.Spider):
    name = "autoria"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/car/used/"]

    def parse(self, response):
        """
        Parse listing page; get car links and paginate.
        """
        logger.info(f"Parsing listing page: {response.url}")
        car_links = response.css("a.address::attr(href)").getall()
        logger.debug(f"Found {len(car_links)} car links")
        for link in car_links:
            yield response.follow(link, callback=self.parse_car)

        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            logger.info(f"Following next page: {next_page}")
            yield response.follow(next_page, callback=self.parse)

    def parse_car(self, response):
        """
        Parse individual car page; extract details and yield item.
        """
        logger.info(f"Parsing car page: {response.url}")
        images = response.css("div.gallery img::attr(src)").getall()
        yield {
            "url": response.url,
            "title": response.css("h1.head::text").get(),
            "price_usd": self.extract_price(response),
            "odometer": self.extract_odometer(response),
            "username": response.css("div.seller_info_name span::text").get(),
            "phone_number": self.extract_phone(response),
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

    def extract_price(self, response):
        """
        Extract price from page, convert to int if possible.
        """
        logger.info("Starting price extraction")

        price_text = response.css("div.price_value strong::text").get()
        logger.debug(f"Raw price text extracted: {price_text}")

        if price_text is None:
            logger.error("Price text is None (not found in page)")
        else:
            logger.info(f"Price text before cleaning: '{price_text}'")

        if price_text:
            digits = "".join(filter(str.isdigit, price_text))
            logger.debug(f"Digits extracted from price text: {digits}")

            if digits:
                try:
                    price = int(digits)
                    logger.info(f"Parsed price as int: {price}")
                    return price
                except ValueError as e:
                    logger.error(f"Failed to convert digits to int: {e}")
            else:
                logger.warning("No digits found in price text")
        else:
            logger.warning("Price text is empty or None")

        logger.warning("Price not found or invalid")
        return None

    def extract_odometer(self, response):
        """
        Extract odometer reading and convert to integer kilometers.
        """
        odo_text = response.xpath(
            "//li[contains(text(),'пробіг') or contains(text(),'пробег')]/strong/text()"
        ).get()
        logger.debug(f"Extracting odometer from text: {odo_text}")
        if odo_text:
            digits = "".join(filter(str.isdigit, odo_text))
            if digits:
                odo = int(digits) * 1000 if "тис" in odo_text else int(digits)
                logger.debug(f"Parsed odometer: {odo}")
                return odo
        logger.warning("Odometer not found or invalid")
        return None

    def extract_phone(self, response):
        """
        Extract phone number; may require additional handling.
        """
        logger.info("Extracting phone number (not implemented)")
        # Placeholder: real extraction might need JavaScript handling
        return None
