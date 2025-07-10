import re

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
)

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


def find_and_click_reveal_button(driver, wait_time=4):
    reveal_selectors = [
        "a.phone_show_link",
        'button.size-large.conversion[data-action="showBottomPopUp"]',
    ]
    for selector in reveal_selectors:
        try:
            logger.info(f"Waiting for element: {selector}")
            element = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            logger.info(f"Found reveal button: {selector}")
            try:
                driver.execute_script("arguments[0].click();", element)
            except StaleElementReferenceException:
                logger.warning(
                    "StaleElementReferenceException caught. Retrying click..."
                )
                element = WebDriverWait(driver, wait_time).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                driver.execute_script("arguments[0].click();", element)
            logger.info(f"Clicked reveal button: {selector}")
            return True
        except TimeoutException:
            logger.debug(f"Element not found: {selector}")
        except Exception as e:
            logger.error(f"Error clicking reveal button: {e}")
    logger.warning("No phone reveal button was found.")
    return False


def wait_for_phone_display(driver, wait_time=4):
    """
    Waits for a full phone number to be visible on the page.
    """
    phone_number_selectors = [
        "div.popup-successful-call-desk",
        'button.size-large.conversion[data-action="call"] span.common-text.ws-pre-wrap.action',
    ]
    for selector in phone_number_selectors:
        try:
            logger.info(f"Waiting for phone number element: {selector}")
            element = WebDriverWait(driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            logger.info(f"Phone number element appeared: {selector}")
            # Log element's outerHTML for debugging
            outer_html = driver.execute_script(
                "return arguments[0].outerHTML;", element
            )
            logger.debug(f"Phone element HTML: {outer_html}")
            return element
        except TimeoutException:
            logger.debug(f"Phone number not found in: {selector}")
    logger.warning("Failed to find phone number after clicking.")
    return None


def extract_phone(driver, url, wait_time=4):
    logger.info(f"Extracting phone number from {url}")
    driver.get(url)

    global popup_handled
    if not popup_handled:
        popup_handled = handle_consent_popup(driver, wait_time)
        logger.info("Handled consent popup for the first time")
    else:
        wait_time = 5

    # Step 1: Click on phone reveal trigger
    clicked = find_and_click_reveal_button(driver, wait_time)
    if not clicked:
        logger.error("Failed to click reveal button.")
        return None
    else:
        logger.info("Reveal button clicked successfully.")

    # Step 2: Wait for full phone number to appear
    phone_element = wait_for_phone_display(driver, wait_time)
    if not phone_element:
        logger.error(
            "Phone element did not appear after clicking reveal button."
        )
        return None

    # Try to extract from div (popup) or span (button)
    try:
        if phone_element.tag_name == "div":
            phone_number = (
                phone_element.get_attribute("data-value")
                or phone_element.text.strip()
            )
        else:
            phone_number = phone_element.text.strip()

        if phone_number:
            logger.info(f"Extracted phone number: {phone_number}")
            return phone_number
        else:
            logger.warning("Phone number text was empty after extraction.")
    except Exception as e:
        logger.error(f"Error extracting phone number text: {e}")

    logger.warning("Failed to extract phone number text.")
    return None


def clean_phone(phone_raw):
    """Normalize phone number digits."""
    logger.debug(f"Raw phone input: {phone_raw}")
    digits = re.sub(r"\D", "", phone_raw)  # remove non-digits
    if digits.startswith("0"):
        digits = "380" + digits[1:]  # add country code
    logger.debug(f"Cleaned phone number: {digits}")
    return digits
