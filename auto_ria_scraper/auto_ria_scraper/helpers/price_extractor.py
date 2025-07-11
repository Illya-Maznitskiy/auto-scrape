import re

from logs.logger import logger


def extract_price(response):
    """
    Extract USD price from the response.
    """
    logger.info("Starting price extraction for all items")

    span_prices = response.css("span[data-currency='USD']::text").getall()
    logger.debug(
        f"Found {len(span_prices)} price texts in "
        f"<span data-currency='USD'>: {span_prices}"
    )

    if not span_prices:
        strong_prices = response.css("strong::text").re(r"[\d\s]+[$]")
        logger.debug(
            f"Found {len(strong_prices)} price texts in "
            f"<strong>: {strong_prices}"
        )
    else:
        strong_prices = []

    all_prices = span_prices if span_prices else strong_prices

    # Clean prices: remove spaces, non-breaking spaces,
    # $ sign, and any other non-digit chars
    cleaned_prices = []
    for price in all_prices:
        # Remove spaces (normal and non-breaking), $ sign,
        # and anything except digits
        cleaned = re.sub(r"\D", "", price)
        cleaned_prices.append(cleaned)

    logger.info(f"Extracted USD prices (cleaned): {cleaned_prices}")

    if cleaned_prices and cleaned_prices[0]:
        return cleaned_prices[0]
    return None
