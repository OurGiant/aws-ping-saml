# coding=utf-8
import uuid

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common import exceptions as se

from version import __version__
import Utilities

log_stream = Utilities.Logging('providers')

saml_page_title = "Amazon Web Services Sign-In"
xpath_locator = By.XPATH
css_locator = By.CLASS_NAME
id_locator = By.ID


class UseIdP:

    @staticmethod
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

        username_next_button = wait.until(ec.element_to_be_clickable((xpath_locator, username_next_button)))
        log_stream.info('Use Okta Login')
        try:
            # Enter the username and click the "Next" button
            log_stream.info('Enter Username')
            username_dialog = driver.find_element(id_locator, username_field)
            username_dialog.clear()
            username_dialog.send_keys(username)
            log_stream.info('Click Button')
            username_next_button.click()
        except se.NoSuchElementException:
            saml_response = "CouldNotEnterFormData"
            return saml_response

        try:
            # Select the "Use password" option and click it
            use_password_button = wait.until(ec.element_to_be_clickable((xpath_locator, select_use_password)))
            log_stream.info('Select Password Entry')
            # css_selector = use_password_button.get_attribute('css_selector')
            # log_stream.info('Use password button css selector' + str(css_selector))
            use_password_button.click()
        except se.ElementClickInterceptedException:
            saml_response = "CouldNotEnterFormData"
            return saml_response

        try:
            # Enter the password and click the "Next" button
            log_stream.info('Enter Password')
            password_dialog = wait.until(ec.element_to_be_clickable((By.ID, password_field)))
            password_dialog.clear()
            password_dialog.send_keys(password)
            log_stream.info('Click Button')
            password_next_button = driver.find_element(By.XPATH, password_next_button)
            password_next_button.click()
        except se.NoSuchElementException:
            saml_response = "CouldNotEnterFormData"
            return saml_response

        try:
            # Select the push notification option and click it
            log_stream.info('Select Push Notification')
            send_push_notification = wait.until(ec.element_to_be_clickable((By.XPATH, select_push_notification)))
            # css_selector = send_push_notification.get_attribute('css_selector')
            # log_stream.info('send push notification css selector' + str(css_selector))
            send_push_notification.click()
        except se.ElementClickInterceptedException:
            saml_response = "CouldNotEnterFormData"
            return saml_response
        try:
            completed_login = wait.until(ec.title_is(saml_page_title))
        except se.TimeoutException:
            log_stream.info('Timeout waiting for MFA')
            log_stream.info('Saving screenshot for debugging')
            screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
            driver.save_screenshot(screenshot)
            raise SystemExit(1)
        return completed_login

    @staticmethod
    def ping_sign_in(wait, driver, username, password, completed_login=False, saml_response=None):
        global saml_page_title
        textbox_username = "username"
        textbox_password = "password"
        button_signon = 'ping-button'

        sign_on_button = wait.until(ec.element_to_be_clickable((css_locator, button_signon)))
        log_stream.info('Use Federated Login Page')
        try:
            log_stream.info('Enter Username')
            username_dialog = driver.find_element(id_locator, textbox_username)
            username_dialog.clear()
            username_dialog.send_keys(username)
        except se.NoSuchElementException:
            saml_response = "CouldNotEnterFormData"
            return saml_response
        try:
            log_stream.info('Enter Password')
            password_dialog = driver.find_element(id_locator, textbox_password)
            password_dialog.clear()
            password_dialog.send_keys(password)
        except se.NoSuchElementException:
            saml_response = "CouldNotEnterFormData"
            return saml_response
        try:
            log_stream.info('Click Button')
            sign_on_button.click()
        except se.ElementClickInterceptedException:
            saml_response = "CouldNotEnterFormData"
            return saml_response
        try:
            completed_login = wait.until(ec.title_is(saml_page_title))
        except se.TimeoutException:
            try:
                log_stream.info('Button did not respond to click, press enter in password field')
                password_dialog.send_keys(Keys.ENTER)
                completed_login = wait.until(ec.title_is(saml_page_title))
            except se.TimeoutException as mfa_timeout_error:
                log_stream.info('Timeout waiting for MFA: ' + str(mfa_timeout_error))
                log_stream.info('Saving screenshot for debugging')
                screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
                driver.save_screenshot(screenshot)
        return completed_login
