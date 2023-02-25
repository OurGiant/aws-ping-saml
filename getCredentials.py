# coding=utf-8
import json

from boto3 import Session as BotoSession
from botocore import errorfactory as err

import Utilities
from Login import IdPLogin
from Config import Config
import Password
import SAMLSelector
from AWS import STS

from version import __version__

log_stream = Utilities.Logging('get_credentials')

args = Utilities.Arguments()
config = Config()
login = IdPLogin()

use_debug, use_gui, browser_type, aws_profile_name, store_password, \
    arg_session_duration, arg_aws_region, text_menu, use_idp, arg_username = args.parse_args()


def get_aws_variables(conf_region, conf_duration):
    if conf_region == "None" and arg_aws_region == "None":
        log_stream.info('Defaulting the region to us-east-1')
        log_stream.info('A custom region may be provided using the config file or the command line argument.')
        aws_region = 'us-east-1'
    elif arg_aws_region == "None":
        aws_region = conf_region
    else:
        aws_region = arg_aws_region

    if conf_duration is None and arg_session_duration == 0:
        log_stream.info('Defaulting the session duration to one hour')
        log_stream.info('A custom duration may be provided using the config file or the command line argument.')
        aws_session_duration = 3600
    elif arg_session_duration is None:
        aws_session_duration = conf_duration
    else:
        aws_session_duration = arg_session_duration

    return aws_region, aws_session_duration


def get_aws_caller_id(profile):
    post_session = BotoSession(profile_name=profile)
    sts = post_session.client('sts')

    aws_caller_identity = sts.get_caller_identity()
    aws_user_id = str(aws_caller_identity['UserId']).split(":", 1)[1]

    return aws_user_id


def main():
    driver_executable = config.verify_drivers(browser_type)

    principle_arn, role_arn, username, config_aws_region, first_page, config_session_duration, \
        saml_provider_name, idp_login_title, gui_name = config.read_config(aws_profile_name,
                                                                           text_menu, use_idp, arg_username)

    aws_region, aws_session_duration = get_aws_variables(config_aws_region, config_session_duration)

    pass_key, pass_file = config.return_stored_pass_config()

    if store_password is False:
        password = Password.get_password()
        if password == "revoke":
            config.revoke_creds(aws_profile_name)
            raise SystemExit(1)

        confirm_store: str = input('Would you like to store this password for future use? [Y/N]')

        if confirm_store == 'Y' or confirm_store == 'y':
            Password.store_password(password, pass_key, pass_file)
    else:
        password: str = Password.retrieve_password(pass_key, pass_file)

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

    log_stream.info('SAML Response Size: ' + str(len(saml_response)))

    if text_menu is True:
        account_map_file = config.return_account_map_file()
        try:
            with open(account_map_file, 'r') as mapfile:
                account_map = json.loads(mapfile.read())
            mapfile.close()
        except FileNotFoundError:
            log_stream.warning('No map file found, using account numbers in display')
            log_stream.warning('The accounts map configuration can be provided to you by your AWS team')
            account_map = None

        all_roles, table_object = SAMLSelector.get_roles_from_saml_response(saml_response, account_map)
        selected_role = SAMLSelector.select_role_from_text_menu(all_roles, table_object)
        role_arn = selected_role['arn']
        principle_arn = selected_role['principle']

    get_sts = STS.aws_assume_role(aws_region, role_arn, principle_arn, saml_response, aws_session_duration)

    if len(get_sts) > 0:
        aws_access_id, aws_secret_key, aws_session_token, sts_expiration, \
            profile_block = STS.get_sts_details(get_sts, aws_region, aws_profile_name)

        if config.validate_aws_cred_format(aws_access_id, aws_secret_key, aws_session_token):
            config.write_config(aws_access_id, aws_secret_key, aws_session_token, aws_profile_name, aws_region)
        else:
            log_stream.critical('There seems to be an issue with one of the credentials generated, please try again')
            raise SystemExit(1)

        aws_user_id = get_aws_caller_id(aws_profile_name)

        sts_expires_local_time: str = sts_expiration.strftime("%c")
        log_stream.info('Token issued for ' + aws_user_id + ' in account ')
        log_stream.info('Token will expire at ' + sts_expires_local_time)

        print(f'\n{profile_block}\n')

    else:
        log_stream.critical("Corrupt or Unavailable STS Response")
        raise SystemExit(1)


if __name__ == "__main__":
    log_stream.info('start login process')
    main()
