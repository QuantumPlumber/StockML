import script_context

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
    def __init__(self):
        pass

    def open_browser(self):
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
        print(self.authenticate_url)

        # go to the url
        self.browser.visit(self.authenticate_url)

    def login(self):
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
        print('accepting MamothAlgo...')

        self.browser.find_by_id('accept').first.click()

        # get url code
        time.sleep(1)
        new_url = self.browser.url

        self.parse_url = urllib.parse.unquote(new_url.split('code=')[1])

        # close browser

        self.browser.quit()

        print(self.parse_url)

        '''
        time.sleep(1)
        print('selecting secret question...')
        self.browser.find_by_text('Can\'t get the text message?').first.click()
        self.browser.find_by_value('Answer a security question').first.click()

        time.sleep(1)
        print('answering secret question...')
        for question, answer in secretQ.items():
            if self.browser.is_text_present(question):
                self.browser.find_by_id('secretquestion').first.fill(answer)
                break

        self.browser.find_by_id('accept').first.click()

        time.sleep(1)
        print('accepting MamothAlgo...')

        self.browser.find_by_id('accept').first.click()
        '''

    def authenticate(self):
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
        authenticate_reply = requests.post(self.token_endpoint, headers=headers, data=payload)

        # convert json reply to dictionary
        self.token_data = authenticate_reply.json()
        self.access_token = self.token_data['access_token']
        self.access_header = {'Authorization': "Bearer {}".format(self.access_token)}
        print(self.access_header)

    def access_accounts(self):
        # define the accounts endpoint
        self.account_endpoint = r'https://api.tdameritrade.com/v1/accounts'

        # POST data to get access token
        self.account_reply = requests.get(url=self.account_endpoint, headers=self.access_header)
        self.account_reply.status_code

        self.account_data = self.account_reply.json()
        print(self.account_data)

        self.account_id = self.account_data[0]['securitiesAccount']['accountId']

    def access_single_account(self, account_id):
        # define the accounts endpoint
        self.account_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}'.format(account_id)

        # POST data to get access token
        self.account_reply = requests.get(url=self.account_endpoint, headers=self.access_header)
        self.account_reply.status_code

        self.account_data = self.account_reply.json()
        print(self.account_data)

        self.account_id = self.account_data[0]['securitiesAccount']['accountId']





    def test(self):
        self.open_browser()
        self.login()
        self.authenticate()
        self.access_account()


if __name__ == "__main__":
    login_instance = login_class()
    login_instance.test()
