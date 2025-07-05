from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
)
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from logs.logger import logger


def get_chrome_driver(headless=True):
    """
    Returns a Chrome WebDriver instance.
    """
    logger.info(f"Initializing Chrome driver with headless={headless}")
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def wait_for_clickable(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """
    Wait for an element to be clickable.
    """
    wait = WebDriverWait(driver, timeout)
    try:
        element = wait.until(ec.element_to_be_clickable((by, selector)))
        logger.info(f"Element is clickable: {selector}")
        return element
    except TimeoutException:
        logger.warning(f"Timeout waiting for clickable element: {selector}")
        return None


def click_element_safe(driver, selector, by=By.CSS_SELECTOR, timeout=10):
    """
    Wait for element to be clickable and click it.
    """
    element = wait_for_clickable(driver, selector, by, timeout)
    if element:
        try:
            element.click()
            logger.info(f"Clicked element: {selector}")
            return True
        except Exception as e:
            logger.error(f"Failed to click element {selector}: {e}")
    else:
        logger.warning(
            f"Element not found or not clickable to click: {selector}"
        )
    return False


def handle_consent_popup(driver, wait_time=1):
    """Detect and dismiss consent popups by clicking or removing them."""
    wait = WebDriverWait(driver, wait_time)

    # Quick existence check - avoid waiting for element if not present
    try:
        driver.find_element(By.CSS_SELECTOR, ".fc-dialog, .fc-dialog-overlay")
    except NoSuchElementException:
        # No popup found, return immediately
        return False

    consent_selectors = [
        "//p[co ntains(@class, 'fc-button-label') and text()='Consent']",
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
            wait.until(ec.invisibility_of_element(btn))
            logger.info(f"Clicked consent popup button with xpath: {xpath}")
            return True
        except TimeoutException:
            continue

    try:
        overlay = wait.until(
            ec.element_to_be_clickable((By.CSS_SELECTOR, ".fc-dialog-overlay"))
        )
        overlay.click()
        wait.until(ec.invisibility_of_element(overlay))
        logger.info("Clicked consent overlay to close popup")
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
