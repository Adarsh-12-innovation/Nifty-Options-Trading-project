import os
import platform
import logging
import traceback
from typing import Tuple, Any, Union
from cryptography.fernet import Fernet
import configparser
import pyotp
import urllib.parse as urlparse
from time import sleep
from inspect import getsourcefile
from os.path import abspath
from kiteconnect import KiteConnect
from pyotp import TOTP
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from fileUtls import is_file_created_or_modified_today
from global_strings import config_file, encryption_key, kite_creds_file, base_path

otp_input_types = ['\'number\'', '\'text\'']


def get_link():
    try:
        with open(kite_creds_file) as kite_credentials:
            kite_credentials_str = kite_credentials.read()
        api_key, api_secret, account_username, account_password, totp = kite_credentials_str.split('\n')[:5]
        kite = KiteConnect(api_key=api_key)
        url = kite.login_url()
        return url
    except Exception as e:
        print(traceback.format_exc())
        return "Following exception occurred while generating link \n" + e.__str__()



def get_otp_object() -> Union[TOTP, str]:
    try:
        with open(kite_creds_file) as kite_credentials:
            kite_credentials_str = kite_credentials.read()
            api_key_, api_secret, account_username, account_password, totp = kite_credentials_str.split('\n')[:5]
            ##get totp generator
            auth_otp = pyotp.TOTP(totp)
            return auth_otp
    except Exception as e:
        print(traceback.format_exc())
        return " Following exception occurred while generating totp \n" + e.__str__()


def get_otp():
    auth_otp = get_otp_object()
    return auth_otp.now()


def get_request_token():
    try:
        with open(kite_creds_file) as kite_credentials:
            kite_credentials_str = kite_credentials.read()
        api_key_, api_secret, account_username, account_password, totp = kite_credentials_str.split('\n')[:5]
        #account_password = getPassword()

        ##set kite login page
        url = get_link()

        ##get otp_object
        auth_otp = get_otp_object()

        ##no gui
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')  # Enable headless mode
        chrome_options.add_argument('--disable-gpu')

        ##open the page
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        ##page 1
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='login-form']")))
        driver.find_element('xpath', '//input[@type=\'text\']').send_keys(account_username)
        driver.find_element('xpath', '//input[@type=\'password\']').send_keys(account_password)
        driver.find_element('xpath', '//button[@type=\'submit\']').click()
        sleep(1)
        ##page 2
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//div[@class='login-form']")))

        set_ = 0
        for otp_input_type in otp_input_types:
            try:
                driver.find_element('xpath', '//input[@type=' + otp_input_type + ']').send_keys(auth_otp.now())
                set_ = 1
                break  # Stop looping if parsing succeeds
            except Exception as e:
                print(f"An unexpected exception occurred: {e}")
                print(traceback.format_exc())

        if set_ == 0:
            return None, None

        driver.find_element('xpath', '//button[@type=\'submit\']').click()
        sleep(1)

        ##page 3
        request_token_ = urlparse.parse_qs(urlparse.urlparse(driver.current_url).query)['request_token'][0]
        return request_token_
    except Exception as e:
        print(traceback.format_exc())
        return " Following exception occurred while getting request token \n" + e.__str__()


def get_access_token(request_token_=None):
    try:
        if request_token_ is None:
            request_token_ = get_request_token()
        with open(kite_creds_file) as kite_credentials:
            kite_credentials_str = kite_credentials.read()
        api_key, api_secret, account_username, account_password, totp = kite_credentials_str.split('\n')[:5]
        kite = KiteConnect(api_key=api_key)
        access_token_ = kite.generate_session(request_token=request_token_, api_secret=api_secret)['access_token']
        return access_token_
    except Exception as e:
        print(traceback.format_exc())
        return " Following exception occurred while getting access token \n" + e.__str__()


def set_access_token(request_token_, access_token_=None):
    try:
        if request_token_ is None:
            request_token_ = get_request_token()
        with open(kite_creds_file) as kite_credentials:
            kite_credentials_str = kite_credentials.read()
        api_key, api_secret, account_username, account_password, totp = kite_credentials_str.split('\n')[:5]
        kite = KiteConnect(api_key=api_key)
        if access_token_ is None:
            access_token_ = kite.generate_session(request_token=request_token_, api_secret=api_secret)['access_token']

        kite.set_access_token(access_token_)
        # refresh text files with new tokens if current token is invalid
        try:
            # Attempt to fetch data using the existing access token
            account_info = kite.ltp("NSE:NIFTY 50")
        except Exception as e:
            print(traceback.format_exc())
            return "Generated access token but it is still invalid \n" + e.__str__()

        with open(os.path.join(base_path, "key", "access_token.txt"), "w") as f:
            f.write(f"{access_token_}")
        with open(os.path.join(base_path, "key", "request_token.txt"), "w") as f:
            f.write(f"{request_token_}")

        return "Generated valid access token"

    except Exception as e:
        print(traceback.format_exc())
        return "Following exception occurred while setting access token \n" + e.__str__()


def kite_auto_set() -> tuple[Any, Any]:
    # get request toke
    request_token_ = get_request_token()

    ##set access token
    access_token_ = get_access_token(request_token_)

    return request_token_, access_token_


def kite_auth(wd: str = None) -> Tuple[KiteConnect, str, str]:
    if wd is None:
        wd = base_path
    with open(kite_creds_file) as f:
        f_str = f.read()
    api_key, api_secret, account_username, account_password, totp = f_str.split('\n')[:5]  # Using top 5 lines for secrets

    # Refresh access token in text files if it is from last day
    try:
        if not is_file_created_or_modified_today(os.path.join(wd, "key", "access_token.txt")):
            request_token_, access_token_ = kite_auto_set()
            with open(os.path.join(wd, "key", "access_token.txt"), "w") as f:
                f.write(f"{access_token_}")
            with open(os.path.join(wd, "key", "request_token.txt"), "w") as f:
                f.write(f"{request_token_}")
    except Exception as e:
        print(e)
        print("Access Token Automation Failed, try setting request token manually")
        print(traceback.format_exc())

    # read tokens from text files and set access token
    with open(os.path.join(wd, "key", "access_token.txt")) as f:
        access_token_ = f.read()
    if access_token_ == "":
        kite = KiteConnect(api_key=api_key)
        with open(os.path.join(wd, "key", "request_token.txt")) as f:
            request_token_ = f.read()
        idata = {}
        try:
            idata = kite.generate_session(request_token_, api_secret)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
        if "access_token" in idata:
            access_token_ = idata["access_token"]
            with open(os.path.join(wd, "key", "access_token.txt"), "w") as f:
                f.write(f"{access_token_}")
            kite.set_access_token(access_token_)
        else:
            raise Exception("kite wasn't able to set access_token")
    else:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token_)

        # refresh text files with new tokens if current token is invalid
        try:
            # Attempt to fetch data using the existing access token
            account_info = kite.ltp("NSE:NIFTY 50")
            print("Access token is valid.")
        except Exception as e:
            print(f"Access token is not valid. Refreshing token...")
            print(traceback.format_exc())

            try:
                request_token_, access_token_ = kite_auto_set()
                with open(os.path.join(wd, "key", "access_token.txt"), "w") as f:
                    f.write(f"{access_token_}")
                with open(os.path.join(wd, "key", "request_token.txt"), "w") as f:
                    f.write(f"{request_token_}")
                kite = KiteConnect(api_key=api_key)
                kite.set_access_token(access_token_)
                print("Access token refreshed successfully.")
            except Exception as e:
                print(e)
                print("Access Token Automation Failed, try setting request token manually")
                print(traceback.format_exc())

    return kite, api_key, access_token_


def getPassword() -> str:
    # Read the encryption key from the file (keep this file secure)
    with open(encryption_key,
              'rb') as keyfile:
        key = keyfile.read()

    # Create a configuration object
    config = configparser.ConfigParser()

    # Read the configuration file
    config.read(config_file)

    # Retrieve the encrypted password
    encrypted_password = config.get('Credentials', 'Encrypted_Password')

    # Create a cipher suite with the key
    cipher_suite = Fernet(key)

    # Decrypt the password
    password = cipher_suite.decrypt(encrypted_password.encode()).decode()

    return password


def check_kite_validity(kite_: KiteConnect):
    try:
        # Attempt to fetch data using the existing access token
        account_info = kite_.ltp("NSE:NIFTY 50")
        return True
    except Exception:
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    kite_, api_key_, access_token_ = kite_auth()
    # request_token, access_token = kite_auto_set()
    # print(request_token)
