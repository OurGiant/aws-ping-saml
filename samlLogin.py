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


def pingSignIn(wait, driver, username, password, element=False, samlResponse=None):
    wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ping-button')))
    print(f'Use Federated Login Page')
    try:
        print("Enter Username")
        usernameDialog = driver.find_element(By.ID,"username")
        usernameDialog.clear()
        usernameDialog.send_keys(username)
    except se.NoSuchElementException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse
    try:
        print('Enter Password')
        passwordDialog = driver.find_element(By.ID,"password")
        passwordDialog.clear()
        passwordDialog.send_keys(password)
    except se.NoSuchElementException as e:
        samlResponse = "CouldNotEnterFormData"
        return samlResponse
    try:
        print('Click Button')
        signOnButton = driver.find_element(By.CLASS_NAME,'ping-button')
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
            screenshot = 'failed_login_screenshot-'+str(uuid.uuid4())+'.png'
            driver.save_screenshot(screenshot)
    return element


class SAMLLogin:
    def __init__(self):
        self.timeout = 20
        self.executePath = str(Path(__file__).resolve().parents[0])
        pass

    def browserLogin(self, username, password, firstPage, useDebug, useGUI, profileName, browser, driverExecutable,
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
            firstPage = firstPage[0:8]+username+':'+password+'@'+firstPage[8:]

        if useDebug is False:
            browser_options.add_argument("--headless")
            browser_options.add_argument("--no-sandbox")

        if browser == 'firefox':
            try:
                driver = webdriver.Firefox(executable_path=driverExecutable, options=browser_options)
                driverLoaded = True
            except OSError as e:
                print(f'There is something wrong with the driver installed for {browser}. Please refer to the documentation in the README on how to download and install the correct driver for your operting system {sys.platform}')
                print(str(e))
        elif browser == 'chrome':
            try:
                driver = webdriver.Chrome(executable_path=driverExecutable, options=browser_options)
                driverLoaded = True
            except OSError as e:
                print(f'There is something wrong with the driver installed for {browser}. Please refer to the documentation in the README on how to download and install the correct driver for your operting system {sys.platform}')
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

            if driver.title == "Sign On":
                element = pingSignIn(wait, driver, username, password)
            elif driver.title == "Amazon Web Services Sign-In":
                element = True
            else:
                element = False

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
