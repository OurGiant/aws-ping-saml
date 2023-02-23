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


def oktaSignIn(wait, driver, username, password, element=False, samlResponse=None):
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
    except se.NoSuchElementException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse

    try:
        wait.until(ec.element_to_be_clickable((By.XPATH, select_use_password)))
        print('Select Password Entry')
        use_password_button = driver.find_element(By.XPATH, select_use_password)
        use_password_button.click()
    except se.ElementClickInterceptedException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse

    try:
        print("Enter Password")
        wait.until(ec.element_to_be_clickable((By.ID, password_field)))
        password_dialog = driver.find_element(By.ID, password_field)
        password_dialog.clear()
        password_dialog.send_keys(password)
        print('Click Button')
        password_next_button = driver.find_element(By.XPATH, password_next_button)
        password_next_button.click()
    except se.NoSuchElementException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse

    try:
        print('Select Push Notification')
        wait.until(ec.element_to_be_clickable((By.XPATH, select_push_notification)))
        username_next_button = driver.find_element(By.XPATH, select_push_notification)
        username_next_button.click()
    except se.ElementClickInterceptedException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse
    try:
        element = wait.until(ec.title_is("Amazon Web Services Sign-In"))
    except se.TimeoutException as e:
        try:
            print('Button did not respond to click, press enter in password field')
            password_dialog.send_keys(Keys.ENTER)
            element = wait.until(ec.title_is("Amazon Web Services Sign-In"))
        except se.TimeoutException as e:
            print(f'Timeout waiting for MFA: {str(e)}')
            print('Saving screenshot for debugging')
            screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
            driver.save_screenshot(screenshot)
    return element

def pingSignIn(wait, driver, username, password, element=False, samlResponse=None):
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ping-button')))
    print(f'Use Federated Login Page')
    try:
        print("Enter Username")
        usernameDialog = driver.find_element(By.ID, "username")
        usernameDialog.clear()
        usernameDialog.send_keys(username)
    except se.NoSuchElementException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse
    try:
        print('Enter Password')
        passwordDialog = driver.find_element(By.ID, "password")
        passwordDialog.clear()
        passwordDialog.send_keys(password)
    except se.NoSuchElementException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse
    try:
        print('Click Button')
        signOnButton = driver.find_element(By.CLASS_NAME, 'ping-button')
        wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ping-button')))
        signOnButton.click()
    except se.ElementClickInterceptedException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse
    try:
        element = wait.until(ec.title_is("Amazon Web Services Sign-In"))
    except se.TimeoutException as e:
        try:
            print('Button did not respond to click, press enter in password field')
            passwordDialog.send_keys(Keys.ENTER)
            element = wait.until(ec.title_is("Amazon Web Services Sign-In"))
        except se.TimeoutException as e:
            print(f'Timeout waiting for MFA: {str(e)}')
            print('Saving screenshot for debugging')
            screenshot = 'failed_login_screenshot-' + str(uuid.uuid4()) + '.png'
            driver.save_screenshot(screenshot)
    return element


def doPINGLogin(driver, wait, username, password, idp_login_title):
    if driver.title == idp_login_title:
        element = pingSignIn(wait, driver, username, password)
    elif driver.title == "Amazon Web Services Sign-In":
        element = True
    else:
        element = False
    return element


def doOKTALogin(driver, wait, username, password, idp_login_title):
    if driver.title == idp_login_title:
        element = oktaSignIn(wait, driver, username, password)
    elif driver.title == "Amazon Web Services Sign-In":
        element = True
    else:
        element = False
    return element


class SAMLLogin:
    def __init__(self):
        self.timeout = 20
        self.executePath = str(Path(__file__).resolve().parents[0])
        pass

    def browserLogin(self, username, password, firstPage, useDebug, useGUI, profileName, browser, driverExecutable,
                     saml_provider_name, idp_login_title,
                     browser_options=None, driver=None):
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
            firstPage = firstPage[0:8] + username + ':' + password + '@' + firstPage[8:]

        if useDebug is False:
            browser_options.add_argument("--headless")
            browser_options.add_argument("--no-sandbox")

        if browser == 'firefox':
            try:
                driver = webdriver.Firefox(executable_path=driverExecutable, options=browser_options)
                driverLoaded = True
            except OSError as e:
                print(
                    f'There is something wrong with the driver installed for {browser}. Please refer to the documentation in the README on how to download and install the correct driver for your operting system {sys.platform}')
                print(str(e))
        elif browser == 'chrome':
            try:
                driver = webdriver.Chrome(executable_path=driverExecutable, options=browser_options)
                driverLoaded = True
            except OSError as e:
                print(
                    f'There is something wrong with the driver installed for {browser}. Please refer to the documentation in the README on how to download and install the correct driver for your operting system {sys.platform}')
                print(str(e))

        if driverLoaded is True:
            driver.set_window_size(1024, 768)

            wait = WebDriverWait(driver, self.timeout)
            driver.get(firstPage)
            try:
                wait.until(ec.title_contains("Sign"))
            except se.TimeoutException as e:
                samlResponse = "CouldNameLoadSignInPage"

            print(f'Sign In Page Title is {driver.title}')

            if saml_provider_name == 'PING':
                element = doPINGLogin(driver, wait, username, password, idp_login_title)
            if saml_provider_name == 'OKTA':
                element = doOKTALogin(driver, wait, username, password, idp_login_title)

            time.sleep(2)

            if element is True:
                print('Waiting for SAML Response....', end='')
                while len(driver.find_elements(By.XPATH, '//*[@id="saml_form"]/input[@name="SAMLResponse"]')) < 1:
                    print('.', end='')
                samlResponseElement = driver.find_elements(By.XPATH, '//*[@id="saml_form"]/input[@name="SAMLResponse"]')
                samlResponse = samlResponseElement[0].get_attribute("value")
                if useGUI is not True:
                    driver.close()
                else:
                    driver.maximize_window()
                    x = 0
                    samlAccounts = {}
                    while x < len(driver.find_elements(By.CLASS_NAME, "saml-account-name")):
                        samlAccount = str(driver.find_elements(By.CLASS_NAME, "saml-account-name")[x].text)
                        samlAccount = samlAccount.replace('(', '').replace(')', '').replace(':', '')
                        samlAccountName = samlAccount.split(' ')[1]
                        samlAccountToken = samlAccount.split(' ')[2]
                        samlAccounts.update({samlAccountName: samlAccountToken})
                        x += 1
                    IAMRole, guiName = config.getGUICreds(profileName)
                    requestedAccountToken = samlAccounts.get(guiName)

                    print(str(requestedAccountToken))
                    accountRadioId = "arn:aws:iam::" + requestedAccountToken + ":role/" + IAMRole
                    accountRadio = driver.find_element(By.ID, accountRadioId)
                    accountRadio.click()
                    signInButton = driver.find_element(By.ID, "signin_button")
                    signInButton.click()
            else:
                samlResponse = "CouldNotCompleteMFA"
        else:
            samlResponse = "CouldNotLoadWebDriver"
        return samlResponse
