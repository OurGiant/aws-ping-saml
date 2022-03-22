import os
import sys

# from samlConfig import Config, getRegion

class Guide:
    def __init__(self):
        aws_region = prompt('AWS working region [us-east-1]:')
        aws_profile_name = prompt('AWS profile name: [default]')
        aws_account_number = prompt('AWS account number: [default]')
        aws_user_name = prompt('AWS user name:')
        aws_password = prompt('AWS password:')
        session_duration = 9600
        browser = "firefox"
        gui = False
        debug = False
        storedpw = False

        if aws_region is None:
            aws_region = 'us-east-1'

        print(aws_region)
        sys.exit(1)



