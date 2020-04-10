import script_context

from Stonks.utilities import utility_exceptions
from Stonks.utilities.config import apikey, username, password, secretQ
import requests
import pandas as pd
import urllib
from splinter import Browser
from selenium import webdriver

import matplotlib.pyplot as plt
import time
import importlib
import h5py
import os
import time
import sys
import numpy as np
import arrow


class login_class():
    def __init__(self, verbose=True):
        '''
        initialize
        :param verbose: set to True to print all the things


        '''
        self.verbose = bool(verbose)
        self.account_data_dict = {}

        self.account_reply = None  # this variable holds the value for the most recent reply from the API.

    def open_browser(self):
        '''
        Open a browser and navigate the authentication endpoint

        :return: True

        needs error messages
        '''
        # define chrome driver path
        self.executable_path = {'executable_path': r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe'}

        # define some options
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--start_maximized")
        self.options.add_argument("--disable_notifications")

        # create a browser object
        self.browser = Browser("chrome", **self.executable_path, headless=False, options=self.options)

        # Build the url
        method = 'GET'
        self.authenticate_endpoint = 'https://auth.tdameritrade.com/auth?'
        self.client_code = apikey + '@AMER.OAUTHAP'
        payload = {'response_type': 'code',
                   'redirect_uri': 'http://localhost/callback',
                   'client_id': self.client_code}

        built_url_return = requests.Request(method, self.authenticate_endpoint, params=payload).prepare()
        self.authenticate_url = built_url_return.url
        if self.verbose: print(self.authenticate_url)

        # go to the url
        self.browser.visit(self.authenticate_url)

    def login(self):
        '''
        Log in using credentials. Get the access key, parse it.

        :return: True if success, false otherwise, needs work.

        Needs error messages
        '''

        payload = {'username': username,
                   'password': password}
        self.browser.find_by_id('username').first.fill(payload['username'])
        self.browser.find_by_id('password').first.fill(payload['password'])
        self.browser.find_by_id('accept').first.click()

        self.browser.find_by_id('accept').first.click()

        phone_code = input('please enter the code sent to the phone: ')
        self.browser.find_by_id('smscode').first.fill(phone_code)
        self.browser.find_by_id('accept').first.click()

        time.sleep(1)
        if self.verbose: print('accepting MamothAlgo...')

        self.browser.find_by_id('accept').first.click()

        # get url code
        time.sleep(1)
        new_url = self.browser.url

        self.parse_url = urllib.parse.unquote(new_url.split('code=')[1])

        # close browser

        self.browser.quit()

        if self.verbose: print(self.parse_url)

        return True

        '''
        time.sleep(1)
        if self.verbose: print('selecting secret question...')
        self.browser.find_by_text('Can\'t get the text message?').first.click()
        self.browser.find_by_value('Answer a security question').first.click()

        time.sleep(1)
        if self.verbose: print('answering secret question...')
        for question, answer in secretQ.items():
            if self.browser.is_text_present(question):
                self.browser.find_by_id('secretquestion').first.fill(answer)
                break

        self.browser.find_by_id('accept').first.click()

        time.sleep(1)
        if self.verbose: print('accepting MamothAlgo...')

        self.browser.find_by_id('accept').first.click()
        '''

    def authenticate(self):
        '''
        Take the access key and get the access and refresh token for the account.

        :return:
        '''
        # create access point url
        self.token_endpoint = r'https://api.tdameritrade.com/v1/oauth2/token'

        # define headers
        headers = {'content-type': "application/x-www-form-urlencoded"}

        # define payload
        payload = {'grant_type': 'authorization_code',
                   'access_type': 'offline',
                   'code': self.parse_url,
                   'client_id': apikey,
                   'redirect_uri': 'http://localhost/callback'}

        # POST data to get access token
        authenticate_reply = requests.post(url=self.token_endpoint, headers=headers, data=payload)
        if self.authenticate_reply.status_code == utility_exceptions.Access_Success:
            # convert json reply to dictionary
            self.token_data = authenticate_reply.json()
            self.access_token = self.token_data['access_token']
            self.access_header = {'Authorization': "Bearer {}".format(self.access_token)}
            if self.verbose: print(self.access_header)
        else:
            raise utility_exceptions.AccessError(url=self.token_endpoint, headers=headers, data=payload)

    def access_accounts(self):
        '''
        Access accounts to get the account ID

        :return:
        '''

        # define the accounts endpoint
        self.accounts_endpoint = r'https://api.tdameritrade.com/v1/accounts'

        # POST data to get access token
        self.account_reply = requests.get(url=self.accounts_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.Access_Success:
            self.account_data = self.account_reply.json()
            if self.verbose: print(self.account_data)
        else:
            raise utility_exceptions.AccessError(url=self.account_endpoint, headers=self.access_header)

        self.account_id = self.account_data[0]['securitiesAccount']['accountId']

    def access_single_account(self, account_id):
        '''
        Access the single account to get data

        :param account_id:
        :return:
        '''

        # define the accounts endpoint
        try:
            self.account_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}'.format(account_id)
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        # POST data to get access token
        self.account_reply = requests.get(url=self.account_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.Access_Success:
            self.account_data_dict[str(account_id)] = self.account_reply.json()
            if self.verbose: print(self.account_data)
        else:
            raise utility_exceptions.AccessError(url=self.account_endpoint, headers=self.access_header)

    def saved_order(self, payload):
        '''
        Create a saved order

        :return:
        '''

        try:
            self.saved_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders'.format(
                self.account_id)
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        # add a line to describe the type of request to the website
        self.saved_order_access_header = self.access_header.copy()
        self.saved_order_access_header['Content-Type'] = 'application/json'

        # define the payload
        '''
        payload = {
            "complexOrderStrategyType": "NONE",
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": "6.45",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "BUY_TO_OPEN",
                    "quantity": 10,
                    "instrument": {
                        "symbol": "XYZ_032015C49",
                        "assetType": "OPTION"
                    }
                }
            ]
        }
        '''

        # post the request
        self.account_reply = requests.post(url=self.saved_order_endpoint, json=payload,
                                           headers=self.saved_order_access_header)
        if self.account_reply.status_code == utility_exceptions.Access_Success:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(url=self.saved_order_endpoint, json=payload,
                                                 headers=self.saved_order_access_header)

    def delete_saved_order(self, order_id):
        try:
            self.delete_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders/{}'.format(
                self.account_id, order_id)
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        # post the request
        self.account_reply = requests.delete(url=self.save_order_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.Access_Success:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(url=self.save_order_endpoint, headers=self.access_header)

    def get_current_saved_orders(self):
        try:
            self.saved_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders'.format(
                self.account_id)
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        result = requests.get(url=self.saved_order_endpoint, headers=self.access_header)
        if result.status_code == 202:
            self.order_dict = result.json()
            return True
        else:
            raise utility_exceptions.AccessError(ErrorCode=result.status_code,
                                                 url=self.saved_order_endpoint,
                                                 headers=self.access_header)
        # continue

    def place_order(self):
        if not self.account_id:
            self.order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(
                self.account_id)
        else:
            # needs a warning
            pass

        # add a line to describe the type of request to the website
        self.order_access_header = self.access_header.copy()
        self.order_access_header['Content-Type'] = 'application/json'

        # define the payload
        payload = {
            "complexOrderStrategyType": "NONE",
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": "6.45",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "BUY_TO_OPEN",
                    "quantity": 10,
                    "instrument": {
                        "symbol": "XYZ_032015C49",
                        "assetType": "OPTION"
                    }
                }
            ]
        }

        # post the request
        result = requests.post(url=self.order_endpoint, json=payload, headers=self.order_access_header)

        # read out the status of the request
        if self.verbose: print(result.status_code)

    def delete_order(self, order_id):
        if not self.account_id:
            self.delete_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders/{}'.format(
                self.account_id, order_id)
        else:
            # needs a warning
            pass

        # post the request
        result = requests.delete(url=self.save_order_endpoint, headers=self.access_header)

        # read out the status of the request
        # needs warning, or exception.
        if self.verbose: print(result.status_code)

    def test(self):
        self.open_browser()
        self.login()
        self.authenticate()
        self.access_account()


if __name__ == "__main__":
    login_instance = login_class()
    # login_instance.test()
