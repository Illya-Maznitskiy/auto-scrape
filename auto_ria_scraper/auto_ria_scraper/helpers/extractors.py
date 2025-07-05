import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from logs.logger import logger


popup_handled = False


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
    cleaned_prices = [
        price.replace(" ", "").replace("$", "") for price in all_prices
    ]
    logger.info(f"Extracted USD prices: {cleaned_prices}")

    if cleaned_prices:
        return cleaned_prices[0]
    return None


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


def handle_consent_popup(driver, wait_time=1):
    """
    Attempts to close or reject cookie/consent popups
    using multiple strategies.
    """
    wait = WebDriverWait(driver, wait_time)

    consent_selectors = [
        "//p[contains(@class, 'fc-button-label') and text()='Consent']",
        "//p[contains(text(), 'Consent')]",
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Do not consent')]",
        "//button[contains(text(), 'Reject')]",
        "//button[contains(text(), 'Close')]",
        "//a[contains(text(), 'Close')]",
    ]

    for xpath in consent_selectors:
        try:
            btn = wait.until(ec.element_to_be_clickable((By.XPATH, xpath)))
            btn.click()
            logger.info(f"Clicked consent popup button with xpath: {xpath}")
            wait.until(ec.invisibility_of_element(btn))
            return True
        except TimeoutException:
            continue

    try:
        overlay = wait.until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, ".fc-dialog-overlay"))
        )
        overlay.click()
        logger.info("Clicked consent overlay to close popup")
        wait.until(ec.invisibility_of_element(overlay))
        return True
    except TimeoutException:
        pass

    try:
        driver.execute_script(
            """
            const overlay = document.querySelector('.fc-dialog-overlay');
            if (overlay) overlay.remove();
            const popup = document.querySelector('.fc-dialog');
            if (popup) popup.remove();
        """
        )
        logger.info("Removed consent popup via JavaScript")
        return True
    except Exception as e:
        logger.warning(f"JS removal of consent popup failed: {e}")

    return False


def extract_phone(driver, url, wait_time=15):
    """
    Extract phone number using Selenium, waiting until
    the phone number is revealed.
    Tries multiple button selectors to handle different page layouts.
    """
    global popup_handled

    logger.info(f"Extracting phone number from {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, wait_time)

        # Only handle popup on the first run
        if not popup_handled:
            popup_handled = handle_consent_popup(driver, wait_time)
            logger.info("Handled consent popup for the first time")

        # List of possible phone reveal button selectors (CSS selectors)
        phone_button_selectors = [
            "a.phone_show_link",
            'button.size-large.conversion[data-action="showBottomPopUp"]',
            'button.size-large.conversion[data-action="call"]',
            "span.conversion_phone_newcars.button.button--green.boxed.mb-16",
        ]

        phone_button = None
        for selector in phone_button_selectors:
            try:
                phone_button = wait.until(
                    ec.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logger.info(
                    f"Found phone reveal button with selector: {selector}"
                )
                driver.execute_script("arguments[0].click();", phone_button)
                logger.info(
                    f"Clicked phone reveal button with selector: {selector}"
                )
                break  # stop trying after successful click
            except TimeoutException:
                logger.debug(
                    f"Phone reveal button not found with selector: {selector}"
                )
                continue

        if not phone_button:
            logger.warning("No phone reveal button found on the page.")
            return None

        # Wait until the phone number is visible in the popup
        wait.until(
            lambda d: d.find_element(
                By.CSS_SELECTOR, "div.popup-successful-call-desk"
            ).get_attribute("data-value")
            != ""
            or d.find_element(
                By.CSS_SELECTOR, "div.popup-successful-call-desk"
            ).text.strip()
            != ""
        )

        phone_div = driver.find_element(
            By.CSS_SELECTOR, "div.popup-successful-call-desk"
        )
        phone_number = (
            phone_div.get_attribute("data-value") or phone_div.text.strip()
        )

        if phone_number:
            logger.info(f"Extracted phone number: {phone_number}")
            return phone_number

        driver.save_screenshot("phone_popup_missing.png")
        logger.warning("Phone number not found. Screenshot saved.")
        return None

    except TimeoutException as e:
        logger.error(f"Timeout extracting phone number: {e}")
        return None

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return None


def clean_phone(phone_raw):
    """Normalize phone number digits."""
    logger.debug(f"Raw phone input: {phone_raw}")
    digits = re.sub(r"\D", "", phone_raw)  # remove non-digits
    if digits.startswith("0"):
        digits = "380" + digits[1:]  # add country code
    logger.debug(f"Cleaned phone number: {digits}")
    return digits
