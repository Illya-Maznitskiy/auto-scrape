import re

from logs.logger import logger


def extract_odometer(response):
    """
    Extract odometer reading from the response.
    Converts 'тыс' to thousands.
    """
    odo_text = response.css("div.bold.dhide::text").get()
    logger.debug(f"Extracting odometer from text: {odo_text}")

    if odo_text:
        odo_text = odo_text.lower().replace("\xa0", " ").strip()
        match = re.search(r"([\d\s]+)", odo_text)
        if match:
            digits_str = match.group(1).replace(" ", "")
            if digits_str.isdigit():
                odo = int(digits_str)
                if "тыс" in odo_text:
                    odo *= 1000
                logger.debug(f"Parsed odometer: {odo}")
                return odo
    logger.warning("Odometer not found or invalid")
    return None
