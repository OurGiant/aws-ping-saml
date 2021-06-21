>>>>>>> 
# AWS SAML Token Utility

This tool is meant to bridge the gap between using federated login for console and CLI access to AWS

## Getting Started

clone this repository to your local system

### Prerequisites
<br>
Requires Python3 latest
<br>
The only drivers included in this distribution are Chrome and Firefox for linux. 
<br>
If you are running this on MacOS or Windows you will need to download the appropriate driver from https://github.com/mozilla/geckodriver or https://chromedriver.chromium.org/downloads. 
<br>
The driver needs to be placed in the 'drivers' directory. The MacOS and Linux drivers do not have an extension, the latest windows drivers for each have the '.exe' extension.
<br>
You must have either Chrome or Firefox installed on your system for this utility to function correctly. Chromium is not supported in the Chrome driver.  
<br>
The config file found in the project root named samlsts will need to be moved to your .aws directory along side your credentials file. This file will need to be configured with the appropriate values, all of which can be found on the SAML page following a successful login.

```
[cloud1-blackbox]
awsRegion = us-east-1
accountNumber = 
IAMRole = PING-Architect
samlProvider = Fed-PING
username=adUsername
guiName=company-blackbox
sessionDuration=14400
```

### Installing

There is a PIP requirements file that must be run before use
```
copy samlsts.demo to ~/.aws/samlsts and adjust configuration based on the values found on the SAML landing page found by visiting the PING loginpage found in the samlsts file
chmod 700 ~/.aws/ (linux/mac)
pip3 install -r requirements.txt
```

### MacOS Users Special Instuctions
After downloading the webdriver to INSTALL_DIR/drivers you may experience a security warning when attempting to execute the utility. To fix this, execute the following
```
xattr -d com.apple.quarantine chromedriver
```
This example is for chromedriver, but will also work on geckdriver (firefox)

## Running the utility

Explain how to run the automated tests for this system

```
python3 getCredentials.py --help
usage: getCredentials.py [-h] [--profilename PROFILENAME] [--browser BROWSER] [--storedpw [STOREDPW]] [--gui [GUI]]
                         --debug DEBUG --duration DURATION

optional arguments:
  -h, --help            show this help message and exit
  --profilename PROFILENAME
                        the AWS profile name for this session
  --browser BROWSER     your browser of choice
  --storedpw [STOREDPW]
                        use a stored password
  --gui [GUI]           open the session in a browser as well
  --debug [DEBUG]       show browser during SAML attempt

```

The profilename should match the profilename in brackets in the samlsts config file.

This utility makes use of Selinium to run a headless browser session for login. Which ever browser is installed and prefered should be used. 
    v1 supports chrome and firefox

The along with creating the credentials in the aws credendial file, the gui option will open a browser with the AWS Console for the profile name selected. This shouldn't be used for long-term operations as the geckodriver browser is not known for speed. This is a quick way to gt a console session while still getting CLI credentials. 

The debug option opens a brower window just before log in allowing the user to track activity then closes once the token is recieved. This a fully interactive browser window. 

### linux/mac shortcut

a fuction alias can be added to .bash_aliased that allows the user to quickrun the utility like

```
getsaml cloud1-prod
getsaml cloud1-prod S (use stored password)
```

```
getsaml() {
	profilename=$1
	if [ $2 ]; then echo "Use stored password"; /usr/bin/python3.8 <INSTALL_DIR>/getCredentials.py --profilename ${profilename} --storedpw --browser firefox; else python3 <INSTALL_DIR>/getCredentials.py --profilename ${profilename} --browser firefox; fi
}

```

Entering a password of 'revoke' will remove the credentials for the given profile


##Troubleshooting


## Built With

* [Python3](https://www.python.org/download/releases/3.0/ )

## Contributing

**Craig Dobson**
<br>
**Tim Dady**
<br>
**Mary James**
<br>
**Basheer Shaik**


## Versioning

version 1.2

## Authors

* **Ryan Leach** - *Initial work*


## License

This project is licensed under the MIT License 

## Acknowledgments


