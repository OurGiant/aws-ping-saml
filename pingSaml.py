import boto3
from botocore import errorfactory as err
import sys
import time

profileName = sys.argv[1]
sleepTimeSeconds = int(sys.argv[2])*60
sleepTimeMinutes = sleepTimeSeconds
maxKeepAlive = int(sys.argv[3])

if sleepTimeMinutes < 3:
    print('Your requested ping time is too aggressive, setting to 5 minutes')
    sleepTime = 5

if maxKeepAlive < sleepTimeMinutes:
    print(f'Your keep alive time {maxKeepAlive} is too short based on your ping time {sleepTimeMinutes} minutes')
    maxKeepAlive = maxKeepAlive*sleepTimeMinutes
    print(f'Setting keep alive to {maxKeepAlive} minutes')


if maxKeepAlive > 120:
    print('Your keep alive time is too aggressive, setting to 120 minutes')
    maxKeepAlive = 120

cycles = round(maxKeepAlive/sleepTimeMinutes)
thisCycle = 0

session = boto3.Session(profile_name=profileName)
sts = session.client('sts')

while True:
    if thisCycle <= cycles:
        try:
            callerIdentity = sts.get_caller_identity()
            userId = str(callerIdentity['UserId']).split(":", 1)[1]
            print(userId)
            thisCycle += 1
            time.sleep(sleepTimeSeconds)
        except err.ClientError as e:
            print(str(e))
            print('Your token has expired')
            False
    else:
        False
