# coding=utf-8
import sys
from boto3 import Session as BotoSession
from botocore import errorfactory as err
from samlLogin import SAMLLogin
from samlConfig import Config, getRegion
from guidedRun import Guide
import passUtils
import argparse

illegalCharacters = ['!', '@', '#', '&', '(', ')', '[', '{', '}', ']', ':', ';', '\'', ',', '?', '/', '\\', '*', '~',
                     '$', '^', '+', '=', '<', '>']

validRegions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

parser = argparse.ArgumentParser()
parser.add_argument("--guideme", type=bool, help="run the utility using prompts")
parser.add_argument("--profilename", type=str, help="the AWS profile name for this session")
parser.add_argument("--region", type=str, help="the AWS profile name for this session")
parser.add_argument("--duration", type=str,  help="desire token length, not to be greater than max length set by AWS administrator")
parser.add_argument("--browser", type=str, help="your browser of choice")
parser.add_argument("--storedpw", type=bool, default=False, nargs='?', const=True, help="use a stored password")
parser.add_argument("--gui", type=bool, default=False, nargs='?', const=True,
                    help="open the session in a browser as well")
parser.add_argument("--debug", type=bool, default=False, nargs='?', const=True, help="show browser during SAML attempt")

if len(sys.argv) == 0:
    print("Arguments required")
    parser.print_help()
    exit(1)
else:
    args = parser.parse_args()

if args.guideme is True:
    guidedRun()
    sys.exit(1)

if args.profilename is None:
    print('A profile name must be specified')
    sys.exit(1)
else:
    profileName = args.profilename
    # profileName = profileName.decode("utf8", "ignore")
    if any(x in profileName for x in illegalCharacters):
        print('bad characters in profilename, only alphanumeric and dash are allowed. ')
        exit(2)

useDebug = args.debug
useGUI = args.gui
browser = args.browser

config = Config()
login = SAMLLogin()

driverExecutable = config.verifyDrivers(browser)

if args.duration is None:
    principleARN, roleARN, username, awsRegion, firstPage, sessionDuration = config.readconfig(profileName)
else:
    principleARN, roleARN, username, awsRegion, firstPage, sessionDuration = config.readconfig(profileName)
    sessionDuration = args.duration


if awsRegion is None and args.region is None:
    print('Defaulting the region to us-east-1\nA custom region may be provided using the config file or the command line arguement.')
    awsRegion = 'us-east-1'

if sessionDuration is None and args.duration is None:
    print('Defaulting the session duration to one hour\nA custom duration may be provided using the config file or the command line arguement.')
    sessionDuration = 3600

passKey, passFile = config.returnStoredPassConfig()

if args.storedpw is False:
    password = passUtils.getPassword()
    if password == "revoke":
        config.revokecreds(profileName)
        exit(0)

    print('Would you like to store this password for future use? [Y/N]')
    confirmStore = input()
    if confirmStore == 'Y' or confirmStore == 'y':
        passUtils.storePass(password, passKey, passFile)
else:
    password = passUtils.retrievePass(passKey, passFile)

try:
    useRegion = getRegion('cli', args)
    validRegions.index(useRegion)
except ValueError:
    print(f'Invalid Region {useRegion}')
    useRegion = getRegion('ask', args)

SAMLResponse = login.browserLogin(username, password, firstPage, useDebug, useGUI, profileName, browser, driverExecutable)

print(f'SAML Response Size: {str(len(SAMLResponse))}')

preSession = BotoSession(region_name=useRegion)
sts = preSession.client('sts')
getSTS = {}

print(f'Role:{roleARN}')
print(f'Principle: {principleARN}')

try:
    getSTS = sts.assume_role_with_saml(
        RoleArn=roleARN,
        PrincipalArn=principleARN,
        SAMLAssertion=SAMLResponse,
        DurationSeconds=int(sessionDuration)
    )
except err.ClientError as e:
    print(f'Error assuming role.\nToken length: {str(len(SAMLResponse))}\nToken string:{str(SAMLResponse)}\n{str(e)}\n')
    exit(2)

if len(getSTS) > 0:
    AccessKeyId = getSTS['Credentials']['AccessKeyId']
    SecretAccessKey = getSTS['Credentials']['SecretAccessKey']
    SessionToken = getSTS['Credentials']['SessionToken']

    profileBlock = "[" + profileName + "]\n" "region = " + useRegion + "\naws_access_key_id =  " + AccessKeyId + "\naws_secret_access_key =  " + SecretAccessKey + "\naws_session_token =  " + SessionToken
    stsExpiration = getSTS['Credentials']['Expiration']

    print(profileBlock)

    config.writeconfig(AccessKeyId, SecretAccessKey, SessionToken, profileName, awsRegion)

    postSession = BotoSession(profile_name=profileName)
    sts = postSession.client('sts')

    callerIdentity = sts.get_caller_identity()
    userId = str(callerIdentity['UserId']).split(":", 1)[1]

    print(f'\n\nToken for {userId} Issued.\n\nToken will expire at {stsExpiration}\n\n')

else:
    print("Corrupt or Unavailable STS Response")
    exit(2)
