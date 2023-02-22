import sys

from cryptography.fernet import Fernet
from cryptography import exceptions as ce
import os
import getpass
from datetime import datetime as dt


def evaluateStore(pass_key):
    safe_perms = 0
    if sys.platform == 'win32':
        safe_perms = 16895
    if sys.platform == 'linux' or sys.platform == 'darwin':
        safe_perms = 16832
    key_path = os.path.dirname(pass_key)
    st = os.stat(key_path)
    mode = int(st.st_mode)
    if mode > safe_perms:
        print(
            f'Permissions on your store directory are too permissive. Please secure this directory from reading by '
            f'anyone other than the owner') 
        exit(1)


def getPassword():
    password = getpass.getpass(prompt='Enter password: ')
    return password


def generateKey(pass_key):
    key = Fernet.generate_key()
    with open(pass_key, "wb") as key_file:
        key_file.write(key)
    return key


def evaluatePass(pass_file, pass_key):
    pass_file_stats = os.stat(pass_file)
    pass_file_age = int(pass_file_stats.st_ctime)
    timestamp_now = int(dt.now().timestamp())
    pass_created = timestamp_now - pass_file_age
    print(f'Password file {pass_file} age: {pass_created}')
    if pass_created > 84600:
        # remove the file, or windows won't be able to create a new one
        try:
            os.remove(pass_file)
        except OSError as e:
            print(f'unable to delete {e}')
        print(f'Your password file is too old. Reenter the password')
        password = getPassword()
        storePass(password, pass_key, pass_file)


def storePass(password, pass_key, pass_file):
    evaluateStore(pass_key)
    key = generateKey(pass_key)
    encoded_pass = password.encode()
    f = Fernet(key)
    encrypted_pass = f.encrypt(encoded_pass)
    with open(pass_file, "wb") as pass_file:
        pass_file.write(encrypted_pass)


def retrievePass(pass_key, pass_file):
    try:
        evaluatePass(pass_file, pass_key)
        key = open(pass_key, "rb").read()
        encrypted_pass = open(pass_file, "rb").read()
    except (OSError, IOError) as e:
        print(f'No password found. A new pass store will be created\n{e}')
        password = getPassword()
        storePass(password, pass_key, pass_file)
        return password
    f = Fernet(key)
    try:
        decrypted_pass = f.decrypt(encrypted_pass)
        return decrypted_pass.decode()
    except ce.InvalidKey as e:
        print(f'Your key is invalid: {str(e)}')
        password = getPassword()
        generateKey(pass_key)
        storePass(password, pass_key, pass_file)
        return password
