import re

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import logging
from logs.logger import logger  # your own logger instance

# Then reduce selenium logs
logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(
    logging.WARNING
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

logger.setLevel(logging.DEBUG)  # set your own logger lev
popup_handled = False


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


def find_clickable_element(driver, selectors, wait_time=5):
    for selector in selectors:
        try:
            element = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            return element, selector
        except TimeoutException:
            continue
    return None, None


def extract_phone(driver, url, wait_time=2):
    logger.info(f"Extracting phone number from {url}")
    driver.get(url)

    global popup_handled
    if not popup_handled:
        popup_handled = handle_consent_popup(driver, wait_time)
        logger.info("Handled consent popup for the first time")

    phone_button_selectors = [
        'button.size-large.conversion[data-action="showBottomPopUp"]',
        "a.phone_show_link",
        'button.size-large.conversion[data-action="call"]',
        "span.conversion_phone_newcars.button.button--green.boxed.mb-16",
    ]

    phone_button, selector = find_clickable_element(
        driver, phone_button_selectors
    )
    if not phone_button:
        logger.warning("No phone reveal button found on page.")
        return None

    logger.info(f"Found and clicking phone button: {selector}")
    driver.execute_script("arguments[0].click();", phone_button)

    # Wait a bit for the full phone number to show up either in a popup or inside the button span
    try:
        # Option 1: Check for popup with full number
        phone_div = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.popup-successful-call-desk")
            )
        )
        phone_number = (
            phone_div.get_attribute("data-value") or phone_div.text.strip()
        )
        if phone_number:
            logger.info(f"Extracted phone number from popup: {phone_number}")
            return phone_number
    except TimeoutException:
        logger.debug("Popup with phone number did not appear.")

    # Option 2: If no popup, try to get phone number from the button's span text (full number after clicking)
    try:
        span = phone_button.find_element(
            By.CSS_SELECTOR, "span.common-text.ws-pre-wrap.action"
        )
        phone_number = span.text.strip()
        if phone_number:
            logger.info(
                f"Extracted phone number from button span: {phone_number}"
            )
            return phone_number
    except Exception:
        logger.debug("Could not get phone number from button span.")

    logger.warning("Failed to extract phone number.")
    return None


def clean_phone(phone_raw):
    """Normalize phone number digits."""
    logger.debug(f"Raw phone input: {phone_raw}")
    digits = re.sub(r"\D", "", phone_raw)  # remove non-digits
    if digits.startswith("0"):
        digits = "380" + digits[1:]  # add country code
    logger.debug(f"Cleaned phone number: {digits}")
    return digits
