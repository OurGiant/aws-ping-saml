import sys

from cryptography.fernet import Fernet
from cryptography import exceptions as ce
import os
import getpass
from datetime import datetime as dt


def evaluateStore(passKey):
    if sys.platform == 'win32':
        safeperms = 16895
    if sys.platform == 'linux' or sys.platform == 'darwin':
        safeperms = 16832
    keyPath = os.path.dirname(passKey)
    st = os.stat(keyPath)
    mode = int(st.st_mode)
    if mode > safeperms:
        print(
            f'Permissions on your store directory are too permissive. Please secure this directory from reading by anyone other than the owner')
        exit(1)


def getPassword():
    password = getpass.getpass(prompt='Enter password: ')
    return password


def generateKey(passKey):
    key = Fernet.generate_key()
    with open(passKey, "wb") as key_file:
        key_file.write(key)
    return key


def evaluatePass(passFile, passKey):
    passFileStats = os.stat(passFile)
    passFileAge = int(passFileStats.st_ctime)
    tsNow = int(dt.now().timestamp())
    passCreated = tsNow - passFileAge
    print(f'Password file age: {passCreated}')
    if passCreated > 86400:
        print(f'Your password file is too old. Reenter the password')
        password = getPassword()
        storePass(password, passKey, passFile)


def storePass(password, passKey, passFile):
    evaluateStore(passKey)
    key = generateKey(passKey)
    encdPass = password.encode()
    f = Fernet(key)
    encryptedPass = f.encrypt(encdPass)
    with open(passFile, "wb") as passFile:
        passFile.write(encryptedPass)


def retrievePass(passKey, passFile):
    try:
        evaluatePass(passFile, passKey)
        key = open(passKey, "rb").read()
        encryptedPass = open(passFile, "rb").read()
    except (OSError, IOError) as e:
        print(f'No password found. A new pass store will be created')
        password = getPassword()
        storePass(password, passKey, passFile)
        return password
    f = Fernet(key)
    try:
        decryptedPass = f.decrypt(encryptedPass)
        return decryptedPass.decode()
    except ce.InvalidKey as e:
        print(f'Your key is invalid: {str(e)}')
        password = getPassword()
        generateKey(passKey)
        storePass(password, passKey, passFile)
        return password
