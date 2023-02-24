import sys
import time
import uuid
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions as se

import SAMLSelector
from version import __version__

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(funcName)s %(levelname)s %(message)s')
logging.getLogger('boto').setLevel(logging.CRITICAL)

saml_page_title = "Amazon Web Services Sign-In"


def okta_sign_in(wait, driver, username, password, completed_login=False, saml_response=None):
    """
    Sign in to Okta using the provided username and password.

    Args:
        wait (WebDriverWait): A WebDriverWait instance used to wait for elements to appear on the page.
        driver (WebDriver): A WebDriver instance used to control the browser.
        username (str): The username to sign in with.
        password (str): The password to sign in with.
        completed_login (bool, optional): Whether the login process has been completed. Defaults to False.
        saml_response (str, optional): The SAML response, if one was received. Defaults to None.

    Returns:
        bool: True if the login process was completed successfully, False otherwise.
    """
    global saml_page_title
    # Define XPath selectors for various page elements
    username_next_button = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input'
    select_use_password = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[3]/div[2]/div[2]'
    password_next_button = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input'
    select_push_notification = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[2]/div[2]/div[2]/a'
    username_field = "input28"
    password_field = "input95"
    wait.until(ec.element_to_be_clickable((By.XPATH, username_next_button)))
    logging.info('Use Okta Login')
    try:
        # Enter the username and click the "Next" button
        logging.info('Enter Username')
        username_dialog = driver.find_element(By.ID, username_field)
        username_dialog.clear()
        username_dialog.send_keys(username)
        logging.info('Click Button')
        username_next_button = driver.find_element(By.XPATH, username_next_button)
        username_next_button.click()
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response

    try:
        # Select the "Use password" option and click it
        wait.until(ec.element_to_be_clickable((By.XPATH, select_use_password)))
        logging.info('Select Password Entry')
        use_password_button = driver.find_element(By.XPATH, select_use_password)
        # css_selector = use_password_button.get_attribute('css_selector')
        # logging.info('Use password button css selector' + str(css_selector))
        use_password_button.click()
    except se.ElementClickInterceptedException:
        saml_response = "CouldNotEnterFormData"
        return saml_response

    try:
        # Enter the password and click the "Next" button
        logging.info('Enter Password')
        wait.until(ec.element_to_be_clickable((By.ID, password_field)))
        password_dialog = driver.find_element(By.ID, password_field)
        password_dialog.clear()
        password_dialog.send_keys(password)
        logging.info('Click Button')
        password_next_button = driver.find_element(By.XPATH, password_next_button)
        password_next_button.click()
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response

    try:
        # Select the push notification option and click it
        logging.info('Select Push Notification')
        wait.until(ec.element_to_be_clickable((By.XPATH, select_push_notification)))
        send_push_notification = driver.find_element(By.XPATH, select_push_notification)
        # css_selector = send_push_notification.get_attribute('css_selector')
        # logging.info('send push notification css selector' + str(css_selector))
        send_push_notification.click()
    except se.ElementClickInterceptedException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        completed_login = wait.until(ec.title_is(saml_page_title))
    except se.TimeoutException:
        logging.info('Timeout waiting for MFA')
        logging.info('Saving screenshot for debugging')
        screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
        driver.save_screenshot(screenshot)
        raise SystemExit(1)
    return completed_login


def ping_sign_in(wait, driver, username, password, completed_login=False, saml_response=None):
    global saml_page_title
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ping-button')))
    logging.info('Use Federated Login Page')
    try:
        logging.info('Enter Username')
        username_dialog = driver.find_element(By.ID, "username")
        username_dialog.clear()
        username_dialog.send_keys(username)
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        logging.info('Enter Password')
        password_dialog = driver.find_element(By.ID, "password")
        password_dialog.clear()
        password_dialog.send_keys(password)
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        logging.info('Click Button')
        sign_on_button = driver.find_element(By.CLASS_NAME, 'ping-button')
        wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ping-button')))
        sign_on_button.click()
    except se.ElementClickInterceptedException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        completed_login = wait.until(ec.title_is("Amazon Web Services Sign-In"))
    except se.TimeoutException:
        try:
            logging.info('Button did not respond to click, press enter in password field')
            password_dialog.send_keys(Keys.ENTER)
            completed_login = wait.until(ec.title_is(saml_page_title))
        except se.TimeoutException as mfa_timeout_error:
            logging.info('Timeout waiting for MFA: ' + str(mfa_timeout_error))
            logging.info('Saving screenshot for debugging')
            screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
            driver.save_screenshot(screenshot)
    return completed_login


def get_saml_response(driver):
    while len(driver.find_elements(By.XPATH, '//*[@id="saml_form"]/input[@name="SAMLResponse"]')) < 1:
        print('.', end='')

    saml_response_completed_login = driver.find_elements(By.XPATH,
                                                         '//*[@id="saml_form"]/input[@name="SAMLResponse"]')

    saml_response = saml_response_completed_login[0].get_attribute("value")

    return saml_response


def missing_browser_message(browser, error):
    message = 'There is something wrong with the driver installed for ' + browser + '.'
    message = message + 'Please refer to the documentation in the README on how to download and '
    message = message + 'install the correct driver for your operating system ' + sys.platform
    logging.critical(message)
    logging.critical(str(error))


def load_browser(browser, driver_executable, use_debug, first_page, username, password):
    is_driver_loaded: bool = False
    browser_options = None

    if browser == 'firefox':
        from selenium.webdriver.firefox.options import Options as Firefox
        browser_options = Firefox()
    elif browser == 'chrome':
        from selenium.webdriver.chrome.options import Options as Chrome
        browser_options = Chrome()
        browser_options.add_argument("--disable-dev-shm-usage")

    if sys.platform == 'win32' and browser == 'chrome':
        try:
            browser_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        except se.NoSuchAttributeException:
            logging.info('Unable to add Experimental Options')
        # Chrome on Win32 requires basic authentication on PING page, prior to form authentication
        first_page = first_page[0:8] + username + ':' + password + '@' + first_page[8:]

    if use_debug is False:
        browser_options.add_argument("--headless")
        browser_options.add_argument("--no-sandbox")

    if browser == 'firefox':
        try:
            driver = webdriver.Firefox(executable_path=driver_executable, options=browser_options)
            is_driver_loaded = True
        except OSError as missing_browser_driver_error:
            missing_browser_message(browser, missing_browser_driver_error)
    elif browser == 'chrome':
        try:
            driver = webdriver.Chrome(executable_path=driver_executable, options=browser_options)
            is_driver_loaded = True
        except OSError as missing_browser_driver_error:
            missing_browser_message(browser, missing_browser_driver_error)

    return driver, is_driver_loaded


class SAMLLogin:
    def __init__(self):
        self.timeout = 20
        self.executePath = str(Path(__file__).resolve().parents[0])
        pass

    def browser_login(self, username, password, first_page, use_debug, use_gui, browser,
                      driver_executable, saml_provider_name, idp_login_title, iam_role, gui_name):

        completed_login: bool = False

        driver, is_driver_loaded = load_browser(browser, driver_executable, use_debug, first_page, username, password)

        if is_driver_loaded is True:
            driver.set_window_size(1024, 768)

            wait = WebDriverWait(driver, self.timeout)
            driver.get(first_page)
            try:
                wait.until(ec.title_contains("Sign"))
            except se.TimeoutException:
                saml_response = "CouldNameLoadSignInPage"
                return saml_response

            logging.info('Sign In Page Title is ' + driver.title)

            if driver.title == idp_login_title:
                if saml_provider_name == 'PING':
                    completed_login = ping_sign_in(wait, driver, username, password)
                if saml_provider_name == 'OKTA':
                    completed_login = okta_sign_in(wait, driver, username, password)
            elif driver.title == "Amazon Web Services Sign-In":
                completed_login = True
            else:
                completed_login = False

            time.sleep(2)

            if completed_login is True:
                logging.info('Waiting for SAML Response.')
                saml_response = get_saml_response(driver)

                if use_gui is not True:
                    driver.close()
                else:
                    SAMLSelector.select_role_from_saml_page(driver, gui_name, iam_role)

            else:
                saml_response = "CouldNotCompleteMFA"
        else:
            saml_response = "CouldNotLoadWebDriver"

        return saml_response
