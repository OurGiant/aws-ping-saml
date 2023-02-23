import configparser
import os
import sys
from pathlib import Path


def missing_config_file_message():
    message = "You are missing the core config file required for the proper operation of this utility.\nThis " \
              "file should be located in the .aws directory, found in your home directory "
    message = message + "\nThis file contains ini style configuration sections containing information about the " \
                        "accounts you are trying to access. "
    message = message + "\nFor example:"
    message = message + "\n\t[cloud1-prod]"
    message = message + "\n\tawsRegion = us-east-1"
    message = message + "\n\taccount_number ="
    message = message + "\n\tIAMRole = PING-DevOps"
    message = message + "\n\tsamlProvider = PING"
    message = message + "\n\tusername=adUsername"
    message = message + "\n\tguiName=production"
    message = message + "\n\tsessionDuration=14400"
    message = message + "\n\nThe configuration must also contain a section for the Authentication provider you " \
                        "are using, ie: PING. Each provider section name must be prefixed with 'Fed-'"
    message = message + "\nFor example:"
    message = message + "\n\t[Fed-PING]"
    message = message + "\n\tloginpage = https: //ping.mycompanydomain.com/idp/ping " \
                        "startSSO.ping?PartnerSpId = urn:amazon: webservices "
    message = message + "\n\nA sample file can be found in the same repository as the utility"
    print(message)
    exit(2)


class Config:
    def __init__(self):

        self.executePath = str(Path(__file__).resolve().parents[0])

        home = str(Path.home())
        self.AWSRoot = home + "/.aws/"
        self.awsSAMLFile = self.AWSRoot + "samlsts"

        # READ IN SAML CONFIG IF EXISTS, EXIT IF NOT
        if Path(self.awsSAMLFile).is_file() is False:
            missing_config_file_message()

        else:
            self.configSAML = configparser.ConfigParser()
            self.configSAML.read(self.awsSAMLFile)

        # READ IN AWS CREDENTIALS
        self.awsCredentialsFile = self.AWSRoot + "credentials"
        if Path(self.awsCredentialsFile).is_file() is True:
            self.configCredentials = configparser.ConfigParser()
            self.configCredentials.read(self.awsCredentialsFile)
        else:
            print(
                f'AWS credentials file {self.awsCredentialsFile} is missing, this is must be the inital run\n'
                f'This program will create an AWS credentials file for you.\n'
            )
            with open(self.awsCredentialsFile, 'w') as creds:
                creds.write("#This is your AWS credentials file\n")
            creds.close()

        self.awsConfigFile = self.AWSRoot + "config"
        if Path(self.awsConfigFile).is_file() is True:
            self.configConfig = configparser.ConfigParser()
            self.configConfig.read(self.awsConfigFile)
        else:
            print(
                f'AWS config file {self.awsConfigFile} is missing, this is must be the inital run\n'
                f'This program will create an AWS config file for you.'
            )

            self.write_aws_config()
            self.configConfig = configparser.ConfigParser()
            self.configConfig.read(self.awsConfigFile)

        self.PassFile = self.AWSRoot + "saml.pass"
        self.PassKey = self.AWSRoot + "saml.key"

    def write_aws_config(self):
        with open(self.awsConfigFile, 'w') as config:
            for section in self.configSAML._sections:
                if section.startswith('Fed-', 0, 4) is False:
                    config.write(
                        "[" + section + "]\nregion=" + self.configSAML._sections[section]['awsregion'] + "\n\n")
        config.close()

    def verify_drivers(self, user_browser, drivers=None, driver=None):
        driver_files = None
        if sys.platform == 'linux' or sys.platform == 'darwin':
            os.environ['PATH'] += ":" + str(Path.cwd()) + '/drivers'
            drivers = self.executePath + '/drivers/'
            driver_files = {'chrome': 'chromedriver', 'firefox': 'geckodriver'}
        elif sys.platform == 'win32':
            os.environ['PATH'] += ";" + str(Path.cwd()) + '\\drivers\\'
            drivers = self.executePath + '\\drivers\\'
            driver_files = {'chrome': 'chromedriver.exe', 'firefox': 'geckodriver.exe'}
        else:
            print(f'Unknown OS type {sys.platform}')
            exit(2)

        try:
            driver = str(drivers + driver_files[user_browser])
        except KeyError:
            print('unknown browser specified.browsers currently supported:')
            for browser, driver in driver_files.items():
                print(browser)
            exit(2)

        if Path(driver).is_file() is False:
            print(f'the driver for browser {user_browser} cannot be found at {str(drivers + driver_files[user_browser])}. '
                  f'Please download the appropriate drive by referencing README.md'
                  )
            exit(2)
        return driver

    def return_stored_pass_config(self):
        return self.PassKey, self.PassFile

    def readconfig(self, aws_profile_name):
        saml_provider = None
        account_number = None
        iam_role = None
        username = None
        try:
            self.configSAML.get(aws_profile_name, 'awsRegion')
        except configparser.NoSectionError as e:
            print(f'No such AWS profile {aws_profile_name}')
            exit(2)
        try:
            aws_region = self.configSAML[aws_profile_name]['awsRegion']
        except KeyError:
            aws_region = None
        try:
            account_number = self.configSAML[aws_profile_name]['accountNumber']
        except KeyError:
            print('An account number must be provided in the configuraton file')
            exit(2)
        try:
            iam_role = self.configSAML[aws_profile_name]['IAMRole']
        except KeyError:
            print('A ROLE number must be provided in the configuraton file')
            exit(2)
        try:
            saml_provider = self.configSAML[aws_profile_name]['samlProvider']
        except KeyError:
            print('A SAML provider must be provided in the configuraton file')
            exit(2)
        try:
            username = self.configSAML[aws_profile_name]['username']
        except KeyError:
            print('A username number must be provided in the configuraton file')
            exit(2)

        try:
            gui_name = self.configSAML[aws_profile_name]['guiName']
        except KeyError:
            print('An account identifier from the SAML form must be provided in the configuraton file')
            exit(2)

        print(f'Reading configuration for SAML provider {saml_provider}')
        first_page = self.configSAML[saml_provider]['loginpage']

        print(f'Reading login title for SAML provider {saml_provider}')
        idp_login_title: str = str(self.configSAML[saml_provider]['loginTitle']).replace('"', '')

        principle_arn = "arn:aws:iam::" + account_number + ":saml-provider/" + saml_provider[4:100]
        role_arn = "arn:aws:iam::" + account_number + ":role/" + iam_role
        try:
            session_duration = self.configSAML[aws_profile_name]['sessionDuration']
        except KeyError:
            session_duration = None

        saml_provider_name = saml_provider.split('-', 1)[1]
        return principle_arn, role_arn, username, aws_region, first_page, session_duration, \
            saml_provider_name, idp_login_title, gui_name

    def get_gui_creds(self, aws_profile_name):
        iam_role = self.configSAML[aws_profile_name]['IAMRole']
        gui_name = self.configSAML[aws_profile_name]['guiName']
        return iam_role, gui_name

    def revoke_creds(self, profile_name):
        self.configCredentials[profile_name] = {}
        self.configConfig["profile " + profile_name] = {}
        with open(self.awsConfigFile, "w") as config:
            self.configConfig.write(config)
        with open(self.awsCredentialsFile, "w") as credentials:
            self.configCredentials.write(credentials)
        print(f'Revoked token for {profile_name}')
        return

    def write_config(self, access_key_id, secret_access_key, aws_session_token, aws_profile_name, aws_region):
        self.configCredentials[aws_profile_name] = {}
        self.configCredentials[aws_profile_name]['aws_access_key_id'] = access_key_id
        self.configCredentials[aws_profile_name]['aws_secret_access_key'] = secret_access_key
        self.configCredentials[aws_profile_name]['aws_session_token'] = aws_session_token

        self.configConfig["profile " + aws_profile_name] = {}
        self.configConfig["profile " + aws_profile_name]['region'] = aws_region

        with open(self.awsConfigFile, "w") as config:
            self.configConfig.write(config)

        with open(self.awsCredentialsFile, "w") as credentials:
            self.configCredentials.write(credentials)
