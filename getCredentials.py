# coding=utf-8
import datetime
import sys
import argparse
import logging


from boto3 import Session as BotoSession
from botocore import errorfactory as err

from samlLogin import SAMLLogin
from samlConfig import Config
import passUtils
import SAMLSelector

from version import __version__

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(funcName)s %(levelname)s %(message)s')
logging.getLogger('boto').setLevel(logging.CRITICAL)


class Utilities:
    def __init__(self):

        self.text_menu = None
        self.aws_region: str = "None"
        self.session_duration: int = 0
        self.store_password: bool = False
        self.aws_profile_name: str = "None"
        self.browser_type: str = "None"
        self.use_gui: bool = False
        self.use_debug: bool = False
        self.illegal_characters = ['!', '@', '#', '&', '(', ')', '[', '{', '}', ']', ':', ';', '\'', ',', '?', '/',
                                   '\\', '*', '~', '$', '^', '+', '=', '<', '>']

        self.valid_regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']

        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--guideme", type=bool, help="run the utility using prompts")
        self.parser.add_argument("--profilename", type=str, help="the AWS profile name for this session")
        self.parser.add_argument("--region", type=str, help="the AWS profile name for this session")
        self.parser.add_argument("--duration", type=str,
                                 help="desire token length, not to be greater than max length set by AWS "
                                      "administrator")
        self.parser.add_argument("--browser", type=str, help="your browser of choice")
        self.parser.add_argument("--storedpw", type=bool, default=False, nargs='?', const=True,
                                 help="use a stored password")
        self.parser.add_argument("--gui", type=bool, default=False, nargs='?', const=True,
                                 help="open the session in a browser as well")
        self.parser.add_argument("--textmenu", type=bool, default=False, nargs='?', const=True,
                                 help="display text menu of accounts. cannot be used with gui option")
        self.parser.add_argument("--debug", type=bool, default=False, nargs='?', const=True,
                                 help="show browser during SAML attempt")
        if len(sys.argv) == 0:
            logging.critical("Arguments required")
            self.parser.print_help()
            raise SystemExit(1)
        else:
            self.args = self.parser.parse_args()

    def parse_args(self):

        # if args.guideme is True:
        #     guidedRun()
        #     sys.exit(1)

        if self.args.profilename == "None":
            logging.critical('A profile name must be specified')
            sys.exit(1)
        else:
            self.aws_profile_name = self.args.profilename
            if any(x in self.aws_profile_name for x in self.illegal_characters):
                logging.critical('bad characters in profile name, only alphanumeric and dash are allowed. ')
                raise SystemExit(1)

        if self.args.gui is True and self.args.textmenu is True:
            logging.critical('You cannot combine GUIT  and Text Menu options. Please choose one or the other')
            raise SystemExit(1)

        self.use_debug = self.args.debug
        self.use_gui = self.args.gui
        self.browser_type = self.args.browser
        self.store_password = self.args.storedpw
        self.session_duration = self.args.duration
        self.aws_region = self.args.region
        self.text_menu = self.args.textmenu

        return self.use_debug, self.use_gui, self.browser_type, self.aws_profile_name, \
            self.store_password, self.session_duration, self.aws_region, self.text_menu


utils = Utilities()
config = Config()
login = SAMLLogin()

use_debug, use_gui, browser_type, aws_profile_name, store_password, \
    arg_session_duration, arg_aws_region, text_menu = utils.parse_args()


def get_aws_variables(conf_region, conf_duration):
    if conf_region == "None" and arg_aws_region == "None":
        logging.info('Defaulting the region to us-east-1')
        logging.info('A custom region may be provided using the config file or the command line argument.')
        aws_region = 'us-east-1'
    elif arg_aws_region == "None":
        aws_region = conf_region
    else:
        aws_region = arg_aws_region

    if conf_duration is None and arg_session_duration == 0:
        logging.info('Defaulting the session duration to one hour')
        logging.info('A custom duration may be provided using the config file or the command line argument.')
        aws_session_duration = 3600
    elif arg_session_duration is None:
        aws_session_duration = conf_duration
    else:
        aws_session_duration = arg_session_duration

    return aws_region, aws_session_duration


def aws_assume_role(region, role, principle, saml_assertion, duration):
    pre_session = BotoSession(region_name=region)
    sts = pre_session.client('sts')
    get_sts = {}

    logging.info('Role: '+role)
    logging.info('Principle: '+principle)

    try:
        get_sts = sts.assume_role_with_saml(
            RoleArn=role,
            PrincipalArn=principle,
            SAMLAssertion=saml_assertion,
            DurationSeconds=int(duration)
        )

    except err.ClientError as e:
        error_message = "Error assuming role. Token length: " + str(len(saml_assertion))
        logging.critical(error_message)
        logging.info(str(saml_assertion))
        logging.critical(str(e))
        exit(2)

    return get_sts


def get_sts_details(sts_object, region):
    aws_access_id = sts_object['Credentials']['AccessKeyId']
    aws_secret_key = sts_object['Credentials']['SecretAccessKey']
    aws_session_token = sts_object['Credentials']['SessionToken']

    profile_block = "[" + aws_profile_name + "]\n" "region = " + region + "\naws_access_key_id =  " + \
                    aws_access_id + "\naws_secret_access_key =  " + aws_secret_key + "\naws_session_token =  " \
                    + aws_session_token

    sts_expiration = sts_object['Credentials']['Expiration']
    local_timezone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    sts_expiration_local = sts_expiration.astimezone(local_timezone)

    return aws_access_id, aws_secret_key, aws_session_token, sts_expiration_local, profile_block


def get_aws_caller_id(profile):
    post_session = BotoSession(profile_name=profile)
    sts = post_session.client('sts')

    aws_caller_identity = sts.get_caller_identity()
    aws_user_id = str(aws_caller_identity['UserId']).split(":", 1)[1]

    return aws_user_id


def main():
    driver_executable = config.verify_drivers(browser_type)

    principle_arn, role_arn, username, config_aws_region, first_page, config_session_duration, \
        saml_provider_name, idp_login_title, gui_name = config.read_config(aws_profile_name)

    aws_region, aws_session_duration = get_aws_variables(config_aws_region, config_session_duration)

    pass_key, pass_file = config.return_stored_pass_config()

    if store_password is False:
        password = passUtils.get_password()
        if password == "revoke":
            config.revoke_creds(aws_profile_name)
            raise SystemExit(1)

        confirm_store: str = input('Would you like to store this password for future use? [Y/N]')

        if confirm_store == 'Y' or confirm_store == 'y':
            passUtils.store_password(password, pass_key, pass_file)
    else:
        password: str = passUtils.retrieve_password(pass_key, pass_file)

    saml_response = login.browser_login(username,
                                        password,
                                        first_page,
                                        use_debug,
                                        use_gui,
                                        browser_type,
                                        driver_executable,
                                        saml_provider_name,
                                        idp_login_title,
                                        role_arn, gui_name)

    logging.info('SAML Response Size: '+str(len(saml_response)))

    if text_menu is True:
        all_roles = SAMLSelector.get_roles_from_saml_response(saml_response)
        selected_role = SAMLSelector.select_role_from_text_menu(all_roles)
        role_arn = selected_role['arn']
        principle_arn = selected_role['principle']


    get_sts = aws_assume_role(aws_region, role_arn, principle_arn, saml_response, aws_session_duration)

    if len(get_sts) > 0:
        aws_access_id, aws_secret_key, aws_session_token, sts_expiration, profile_block = get_sts_details(get_sts, aws_region)

        if config.validate_aws_cred_format(aws_access_id,aws_secret_key,aws_session_token):
            config.write_config(aws_access_id, aws_secret_key, aws_session_token, aws_profile_name, aws_region)
        else:
            logging.critical('There seems to be an issue with one of the credentials generated, please try again')
            raise SystemExit(1)

        aws_user_id = get_aws_caller_id(aws_profile_name)

        sts_expires_local_time: str = sts_expiration.strftime("%c")
        logging.info('Token issued for '+aws_user_id+' in account ')
        logging.info('Token will expire at '+sts_expires_local_time)

        print(f'\n{profile_block}\n')

    else:
        logging.critical("Corrupt or Unavailable STS Response")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
