import sys
import time
from pathlib import Path
import uuid
from selenium import webdriver
from selenium.common import exceptions as se
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from samlConfig import Config

config = Config()


def okta_sign_in(wait, driver, username, password, completed_login=False, saml_response=None):
    username_next_button = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input'
    select_use_password = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[3]/div[2]/div[2]'
    password_next_button = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input'
    select_push_notification = '/html/body/div[2]/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[2]/div[2]/div[2]/a'
    username_field = "input28"
    password_field = "input95"
    wait.until(ec.element_to_be_clickable((By.XPATH, username_next_button)))
    print(f'Use Okta Login')
    try:
        print("Enter Username")
        username_dialog = driver.find_element(By.ID, username_field)
        username_dialog.clear()
        username_dialog.send_keys(username)
        print('Click Button')
        username_next_button = driver.find_element(By.XPATH, username_next_button)
        username_next_button.click()
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response

    try:
        wait.until(ec.element_to_be_clickable((By.XPATH, select_use_password)))
        print('Select Password Entry')
        use_password_button = driver.find_element(By.XPATH, select_use_password)
        use_password_button.click()
    except se.ElementClickInterceptedException:
        saml_response = "CouldNotEnterFormData"
        return saml_response

    try:
        print("Enter Password")
        wait.until(ec.element_to_be_clickable((By.ID, password_field)))
        password_dialog = driver.find_element(By.ID, password_field)
        password_dialog.clear()
        password_dialog.send_keys(password)
        print('Click Button')
        password_next_button = driver.find_element(By.XPATH, password_next_button)
        password_next_button.click()
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response

    try:
        print('Select Push Notification')
        wait.until(ec.element_to_be_clickable((By.XPATH, select_push_notification)))
        username_next_button = driver.find_element(By.XPATH, select_push_notification)
        username_next_button.click()
    except se.ElementClickInterceptedException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        completed_login = wait.until(ec.title_is("Amazon Web Services Sign-In"))
    except se.TimeoutException:
        try:
            print('Button did not respond to click, press enter in password field')
            password_dialog.send_keys(Keys.ENTER)
            completed_login = wait.until(ec.title_is("Amazon Web Services Sign-In"))
        except se.TimeoutException as e:
            print(f'Timeout waiting for MFA: {str(e)}')
            print('Saving screenshot for debugging')
            screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
            driver.save_screenshot(screenshot)
    return completed_login


def ping_sign_in(wait, driver, username, password, completed_login=False, saml_response=None):
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ping-button')))
    print(f'Use Federated Login Page')
    try:
        print("Enter Username")
        username_dialog = driver.find_element(By.ID, "username")
        username_dialog.clear()
        username_dialog.send_keys(username)
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        print('Enter Password')
        password_dialog = driver.find_element(By.ID, "password")
        password_dialog.clear()
        password_dialog.send_keys(password)
    except se.NoSuchElementException:
        saml_response = "CouldNotEnterFormData"
        return saml_response
    try:
        print('Click Button')
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
            print('Button did not respond to click, press enter in password field')
            password_dialog.send_keys(Keys.ENTER)
            completed_login = wait.until(ec.title_is("Amazon Web Services Sign-In"))
        except se.TimeoutException as e:
            print(f'Timeout waiting for MFA: {str(e)}')
            print('Saving screenshot for debugging')
            screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
            driver.save_screenshot(screenshot)
    return completed_login


#
# def use_ping_launch(driver, wait, username, password, idp_login_title):
#     if driver.title == idp_login_title:
#         completed_login = ping_sign_in(wait, driver, username, password)
#     elif driver.title == "Amazon Web Services Sign-In":
#         completed_login = True
#     else:
#         completed_login = False
#     return completed_login
#
#
# def use_okta_launch(driver, wait, username, password, idp_login_title):
#     if driver.title == idp_login_title:
#         completed_login = okta_sign_in(wait, driver, username, password)
#     elif driver.title == "Amazon Web Services Sign-In":
#         completed_login = True
#     else:
#         completed_login = False
#     return completed_login
#

def select_role_from_saml(driver, gui_name, iam_role):
    driver.maximize_window()
    x = 0
    saml_accounts = {}
    while x < len(driver.find_elements(By.CLASS_NAME, "saml-account-name")):
        saml_account = str(driver.find_elements(By.CLASS_NAME, "saml-account-name")[x].text)
        saml_account = saml_account.replace('(', '').replace(')', '').replace(':', '')
        saml_account_name = saml_account.split(' ')[1]
        saml_account_token = saml_account.split(' ')[2]
        saml_accounts.update({saml_account_name: saml_account_token})
        x += 1

    requested_account_token = saml_accounts.get(gui_name)

    print(str(requested_account_token))
    account_radio_id = "arn:aws:iam::" + requested_account_token + ":role/" + iam_role
    account_radio = driver.find_element(By.ID, account_radio_id)
    account_radio.click()
    sign_in_button = driver.find_element(By.ID, "signin_button")
    sign_in_button.click()


def get_saml_response(driver):
    while len(driver.find_elements(By.XPATH, '//*[@id="saml_form"]/input[@name="SAMLResponse"]')) < 1:
        print('.', end='')

    saml_response_completed_login = driver.find_elements(By.XPATH,
                                                         '//*[@id="saml_form"]/input[@name="SAMLResponse"]')

    saml_response = saml_response_completed_login[0].get_attribute("value")

    return saml_response


def load_browser(browser, driver_executable, use_debug, first_page, username, password):
    is_driver_loaded: bool = False

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
            print('Unable to add Experimental Options')
        # Chrome on Win32 requires basic authentication on PING page, prior to form authentication
        first_page = first_page[0:8] + username + ':' + password + '@' + first_page[8:]

    if use_debug is False:
        browser_options.add_argument("--headless")
        browser_options.add_argument("--no-sandbox")

    if browser == 'firefox':
        try:
            driver = webdriver.Firefox(executable_path=driver_executable, options=browser_options)
            is_driver_loaded = True
        except OSError as e:
            print(
                f'There is something wrong with the driver installed for {browser}. '
                f'Please refer to the documentation in the README on how to download and '
                f'install the correct driver for your operting system {sys.platform}')
            print(str(e))
    elif browser == 'chrome':
        try:
            driver = webdriver.Chrome(executable_path=driver_executable, options=browser_options)
            is_driver_loaded = True
        except OSError as e:
            print(
                f'There is something wrong with the driver installed for {browser}. '
                f'Please refer to the documentation in the README on how to download and '
                f'install the correct driver for your operating system {sys.platform}')
            print(str(e))

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

            print(f'Sign In Page Title is {driver.title}')

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
                print('Waiting for SAML Response....', end='')
                saml_response = get_saml_response(driver)
                if use_gui is not True:
                    driver.close()
                else:
                    select_role_from_saml(driver, gui_name, iam_role)
            else:
                saml_response = "CouldNotCompleteMFA"
        else:
            saml_response = "CouldNotLoadWebDriver"

        return saml_response
