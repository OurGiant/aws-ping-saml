import configparser
import os
import sys
from pathlib import Path


def missingConfigFileMessage():
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


def getRegion(type, args, useRegion=None):
    if type == 'cli':
        if args.region is None:
            useRegion = 'us-east-1'
        else:
            useRegion = args.region
    elif type == 'ask':
        useRegion = input('Choose a valid region: [us-east-1, us-east-2, us-west-1, us-west-2 ] ')

    return useRegion


class Config:
    def __init__(self):

        self.executePath = str(Path(__file__).resolve().parents[0])

        home = str(Path.home())
        self.AWSRoot = home + "/.aws/"
        self.awsSAMLFile = self.AWSRoot + "samlsts"

        # READ IN SAML CONFIG IF EXISTS, EXIT IF NOT
        if Path(self.awsSAMLFile).is_file() is False:
            missingConfigFileMessage()

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

            self.writeAWSConfig()
            self.configConfig = configparser.ConfigParser()
            self.configConfig.read(self.awsConfigFile)

        self.PassFile = self.AWSRoot + "saml.pass"
        self.PassKey = self.AWSRoot + "saml.key"

    def writeAWSConfig(self):
        with open(self.awsConfigFile, 'w') as config:
            for section in self.configSAML._sections:
                if section.startswith('Fed-', 0, 4) is False:
                    config.write(
                        "[" + section + "]\nregion=" + self.configSAML._sections[section]['awsregion'] + "\n\n")
        config.close()

    def verifyDrivers(self, userBrowser, drivers=None, driver=None):
        if sys.platform == 'linux' or sys.platform == 'darwin':
            os.environ['PATH'] += ":" + str(Path.cwd()) + '/drivers'
            drivers = self.executePath + '/drivers/'
            driverFiles = {'chrome': 'chromedriver', 'firefox': 'geckodriver'}
        elif sys.platform == 'win32':
            os.environ['PATH'] += ";" + str(Path.cwd()) + '\\drivers\\'
            drivers = self.executePath + '\\drivers\\'
            driverFiles = {'chrome': 'chromedriver.exe', 'firefox': 'geckodriver.exe'}
        else:
            print(f'Unknown OS type {sys.platform}')
            exit(2)

        try:
            driver = str(drivers + driverFiles[userBrowser])
        except KeyError as e:
            print('unknown browser specified.browsers currently supported:')
            for browser, driver in driverFiles.items():
                print(browser)
            exit(2)

        if Path(driver).is_file() is False:
            print(f'the driver for browser {userBrowser} cannot be found at {str(drivers + driverFiles[userBrowser])}. '
                  f'Please download the appropriate drive by referencing README.md'
                  )
            exit(2)
        return driver

    def returnStoredPassConfig(self):
        return self.PassKey, self.PassFile

    def readconfig(self, profileName):
        try:
            self.configSAML.get(profileName, 'awsRegion')
        except configparser.NoSectionError as e:
            print(f'No such AWS profile {profileName}')
            exit(2)
        try:
            awsRegion = self.configSAML[profileName]['awsRegion']
        except KeyError:
            awsRegion = None
        try:
            account_number = self.configSAML[profileName]['accountNumber']
        except KeyError:
            print('An account number must be provided in the configuraton file')
            exit(2)
        try:
            IAMRole = self.configSAML[profileName]['IAMRole']
        except KeyError:
            print('A ROLE number must be provided in the configuraton file')
            exit(2)
        try:
            samlProvider = self.configSAML[profileName]['samlProvider']
        except KeyError:
            print('A SAML provider must be provided in the configuraton file')
            exit(2)
        try:
            username = self.configSAML[profileName]['username']
        except KeyError:
            print('A username number must be provided in the configuraton file')
            exit(2)

        guiName = self.configSAML[profileName]['guiName']

        print(f'Reading configuration for SAML provider {samlProvider}')
        firstPage = self.configSAML[samlProvider]['loginpage']

        print(f'Reading login title for SAML provider {samlProvider}')
        idp_login_title = str(self.configSAML[samlProvider]['loginTitle']).replace('"', '')

        principle_arn = "arn:aws:iam::" + account_number + ":saml-provider/" + samlProvider[4:100]
        roleARN = "arn:aws:iam::" + account_number + ":role/" + IAMRole
        try:
            sessionDuration = self.configSAML[profileName]['sessionDuration']
        except KeyError:
            sessionDuration = None

        saml_provider_name = samlProvider.split('-', 1)[1]
        return principle_arn, roleARN, username, awsRegion, firstPage, sessionDuration, saml_provider_name, idp_login_title

    def getGUICreds(self, profileName):
        IAMRole = self.configSAML[profileName]['IAMRole']
        guiName = self.configSAML[profileName]['guiName']
        return IAMRole, guiName

    def revokecreds(self, profileName):
        self.configCredentials[profileName] = {}
        self.configConfig["profile " + profileName] = {}
        with open(self.awsConfigFile, "w") as config:
            self.configConfig.write(config)
        with open(self.awsCredentialsFile, "w") as credentials:
            self.configCredentials.write(credentials)
        print(f'Revoked token for {profileName}')
        return

    def writeconfig(self, AccessKeyId, SecretAccessKey, SessionToken, profileName, awsRegion):
        self.configCredentials[profileName] = {}
        self.configCredentials[profileName]['aws_access_key_id'] = AccessKeyId
        self.configCredentials[profileName]['aws_secret_access_key'] = SecretAccessKey
        self.configCredentials[profileName]['aws_session_token'] = SessionToken

        self.configConfig["profile " + profileName] = {}
        self.configConfig["profile " + profileName]['region'] = awsRegion

        with open(self.awsConfigFile, "w") as config:
            self.configConfig.write(config)

        with open(self.awsCredentialsFile, "w") as credentials:
            self.configCredentials.write(credentials)
