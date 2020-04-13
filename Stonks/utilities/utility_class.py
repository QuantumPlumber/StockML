import script_context

import Stonks.global_enums as enums
from Stonks.utilities import utility_exceptions
from Stonks.utilities.config import apikey, username, password, secretQ
import requests
import pandas as pd
import urllib
from splinter import Browser
from selenium import webdriver

import importlib
import h5py
import os
import sys
import time
import sys
import arrow

importlib.reload(utility_exceptions)
importlib.reload(enums)


class UtilityClass():
    '''
    This class handles the interface with the TD Ameritrade API and keeps the status of the account and connection.

    It handles requests to the API and has error checking to ensure the program does not hang on API errors.

    '''

    def __init__(self, verbose=True):
        '''
        initialize

        :param verbose: set to True to print all the things


        '''

        ################################################################################################################
        # behavior variables
        ################################################################################################################
        self.verbose = bool(verbose)

        ################################################################################################################
        # login & authentication variables
        ################################################################################################################
        self.account_authenticated = False
        self.refresh_token_filename = 'refToken.txt'

        ################################################################################################################
        # account variables
        ################################################################################################################
        self.account_data_dict = {}

        ################################################################################################################
        # account variables
        ################################################################################################################

        self.account_reply = None  # this variable holds the value for the most recent reply from the API.

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin login functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

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

    def credential(self):
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
        return True

    def authenticate(self):
        '''
        Take the access key and get the access and refresh token for the account.

        :return:
        '''

        try:
            self.parse_url
        except AttributeError:
            if self.verbose: print('token url not parsed')
            raise utility_exceptions.AccountError(parse_url_error=True)

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
        self.authenticate_reply = requests.post(url=self.token_endpoint, headers=headers, data=payload)
        if self.authenticate_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
            # convert json reply to dictionary
            self.token_data = self.authenticate_reply.json()
            self.access_token = self.token_data['access_token']
            self.access_header = {'Authorization': "Bearer {}".format(self.access_token)}
            self.refresh_token = self.token_data['refresh_token']
            if self.verbose: print(self.access_header)

            self.utility_path = os.getcwd()
            filepath = self.utility_path + '/' + self.refresh_token_filename
            file = open(filepath, mode='w')
            file.write(self.refresh_token)
            file.close()

            self.account_authenticated = True

        else:
            raise utility_exceptions.AccessError(url=self.token_endpoint, headers=headers, data=payload)

    def refresh_authentication(self):
        '''
        Use the refresh token to get a new access_token

        :return:
        '''

        try:
            self.refresh_token
        except AttributeError:
            if self.verbose: print('refresh token not initialized')
            raise utility_exceptions.AccountError(refresh_token_error=True)

        # create access point url
        self.token_endpoint = r'https://api.tdameritrade.com/v1/oauth2/token'

        # define headers
        headers = {'content-type': "application/x-www-form-urlencoded"}

        # define payload
        payload = {'grant_type': 'refresh_token',
                   'access_type': 'offline',
                   'refresh_token': self.refresh_token,
                   'client_id': apikey,
                   'redirect_uri': 'http://localhost/callback'}

        # POST data to get access token
        self.authenticate_reply = requests.post(url=self.token_endpoint, headers=headers, data=payload)
        if self.authenticate_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
            # convert json reply to dictionary
            self.token_data = self.authenticate_reply.json()
            self.access_token = self.token_data['access_token']
            self.access_header = {'Authorization': "Bearer {}".format(self.access_token)}
            if self.verbose: print(self.access_header)

            self.account_authenticated = True

        else:
            raise utility_exceptions.AccessError(url=self.token_endpoint, headers=headers, data=payload)

    def check_for_refresh_token(self):
        self.utility_path = os.getcwd()
        filepath = self.utility_path + '/' + self.refresh_token_filename
        if self.verbose: print(filepath)

        if os.path.isfile(filepath):
            file = open(filepath, mode='r')
            if self.verbose: print('opened file at: {}'.format(filepath))
            self.refresh_token = file.readline()
            file.close()
            return True
        else:
            if self.verbose: print('no refresh token file detected at {}'.format(filepath))
            return False

    def login(self):
        if not self.check_for_refresh_token():
            self.open_browser()
            self.credential()
            self.authenticate()
        else:
            self.refresh_authentication()

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin account functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def access_accounts(self):
        '''
        Access accounts to get the account ID

        :return:
        '''

        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        # define the accounts endpoint
        self.accounts_endpoint = r'https://api.tdameritrade.com/v1/accounts'

        # POST data to get access token
        self.account_reply = requests.get(url=self.accounts_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
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

        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        # define the accounts endpoint
        self.account_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}'.format(account_id)

        # POST data to get access token
        self.account_reply = requests.get(url=self.account_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
            self.account_data_dict[str(account_id)] = self.account_reply.json()
            if self.verbose: print(self.account_data)
        else:
            raise utility_exceptions.AccessError(url=self.account_endpoint, headers=self.access_header)

    def get_account(self):
        try:
            self.access_accounts()
        except utility_exceptions.AccountError:
            if self.account_authenticated:
                self.login()
            else:
                raise

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin saved order functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def place_saved_order(self, payload):
        '''
        Create a saved order

        :return:
        '''

        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.saved_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders'.format(
            self.account_id)

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
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(url=self.saved_order_endpoint,
                                                 json=payload,
                                                 headers=self.saved_order_access_header,
                                                 ErrorCode=self.account_reply.status_code)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    def delete_saved_order(self, order_id):
        '''
        Delete a saved order

        :param order_id:
        :return:
        '''
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.delete_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders/{}'.format(
            self.account_id, order_id)

        # post the request
        self.account_reply = requests.delete(url=self.save_order_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(url=self.save_order_endpoint, headers=self.access_header)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    def get_current_saved_orders(self):
        '''
        Get the current saved orders and store them in a dictionary.
        :return:
        '''
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.saved_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders'.format(
            self.account_id)

        self.account_reply = requests.get(url=self.saved_order_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            self.order_dict = self.account_reply.json()
            if self.verbose: print(self.order_dict)
            return True
        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.saved_order_endpoint,
                                                 headers=self.access_header)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    def replace_saved_order(self, order_id, payload):
        '''
        Replace a saved order

        :return:
        '''

        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.saved_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/savedorders/{}'.format(
            self.account_id, order_id)

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
        self.account_reply = requests.put(url=self.saved_order_endpoint, json=payload,
                                          headers=self.saved_order_access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(url=self.saved_order_endpoint, json=payload,
                                                 headers=self.saved_order_access_header)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin order functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def place_order(self, payload):
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders'.format(
            self.account_id)

        # add a line to describe the type of request to the website
        self.order_access_header = self.access_header.copy()
        self.order_access_header['Content-Type'] = 'application/json'

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
        self.account_reply = requests.post(url=self.order_endpoint, json=payload, headers=self.order_access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.order_endpoint,
                                                 headers=self.order_access_header)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    def delete_order(self, order_id):
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.delete_order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders/{}'.format(
            self.account_id, order_id)
        # post the request
        self.account_reply = requests.delete(url=self.delete_order_endpoint, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            if self.verbose: print('deleted order'.format(order_id))
        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.saved_order_endpoint,
                                                 headers=self.access_header)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    def replace_order(self, order_id, payload):
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        try:
            self.account_id
        except AttributeError:
            if self.verbose: print('account id not defined')
            raise utility_exceptions.AccountError(id_error=True)

        self.order_endpoint = r'https://api.tdameritrade.com/v1/accounts/{}/orders/{}'.format(
            self.account_id, order_id)

        # add a line to describe the type of request to the website
        self.order_access_header = self.access_header.copy()
        self.order_access_header['Content-Type'] = 'application/json'

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
        self.account_reply = requests.post(url=self.order_endpoint, json=payload, headers=self.order_access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.order_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)
        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.saved_order_endpoint,
                                                 headers=self.order_access_header)

        # record whether the the order state has changed
        self.orders_state_has_changed = True

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # Begin quote functions

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def get_price_history(self, symbol, payload):
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        self.price_history_endpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/pricehistory'.format(symbol)

        self.account_reply = requests.get(url=self.price_history_endpoint, params=payload, headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)

            return self.account_reply.json()

        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.price_history_endpoint,
                                                 params=payload
                                                 )

        pass

    def get_options_chain(self, payload):
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        self.options_chain_endpoint = r'https://api.tdameritrade.com/v1/marketdata/chains'

        # post the request
        self.account_reply = requests.get(url=self.options_chain_endpoint, params=payload,
                                          headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)

            return self.account_reply.json()

        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.options_chain_endpoint,
                                                 headers=self.options_access_header)

    def get_quote(self, symbol):
        try:
            self.access_header
        except AttributeError:
            if self.verbose: print('access header not defined')
            raise utility_exceptions.AccountError(header_error=True)

        self.quote_endpoint = r'https://api.tdameritrade.com/v1/marketdata/{}/quotes'.format(symbol)

        # add a line to describe the type of request to the website
        self.options_access_header = self.access_header.copy()
        self.options_access_header['Content-Type'] = 'application/json'

        # post the request
        self.account_reply = requests.get(url=self.quote_endpoint,
                                          headers=self.access_header)
        if self.account_reply.status_code == utility_exceptions.AccessSuccess.account_success.value:
            # read out the status of the request
            if self.verbose: print(self.account_reply.status_code)

            return self.account_reply.json()

        else:
            raise utility_exceptions.AccessError(ErrorCode=self.account_reply.status_code,
                                                 url=self.options_chain_endpoint,
                                                 headers=self.options_access_header)

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    # define some built in tests... these should really be scripts

    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################
    ####################################################################################################################

    def test(self):
        self.get_account()

        # self.open_browser()
        # self.login()
        # self.authenticate()
        # self.access_accounts()
        # self.access_single_account(account_id=self.account_id)

    def test_price_history(self):
        # self.login()

        lookback_days = 1
        today = arrow.now('America/New_York')
        today = today.replace(hour=4, minute=0, second=0, microsecond=0)
        yesterday = today.shift(days=-lookback_days)

        payload = {enums.PriceHistoryPayload.apikey.value: apikey,
                   enums.PriceHistoryPayload.periodType.value: enums.PeriodTypeOptions.day.value,
                   enums.PriceHistoryPayload.period.value: 1,
                   enums.PriceHistoryPayload.frequencyType.value: enums.FrequencyTypeOptions.minute.value,
                   enums.PriceHistoryPayload.frequency.value: 1,
                   enums.PriceHistoryPayload.startDate.value: yesterday.timestamp,
                   # 'endDate ': startdate,
                   enums.PriceHistoryPayload.needExtendedHoursData.value: 'false'
                   }

        history = self.get_price_history('SPY', payload=payload)

    def test_options_chain(self):
        today = arrow.now('America/New_York')
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        day_after_tomorrow = today.shift(days=2)
        print(day_after_tomorrow.date())

        payload = {'apikey': apikey,
                   'symbol': 'SPY',
                   'contractType': 'PUT',
                   'strikeCount': 10,
                   'includeQuotes': 'TRUE',
                   'strategy': 'SINGLE',
                   'fromDate': today.format(),
                   'toDate': day_after_tomorrow.format()}

        payload = {'symbol': 'SPY',
                   'contractType': 'PUT',
                   'strikeCount': 10,
                   'includeQuotes': 'TRUE',
                   'strategy': 'SINGLE',
                   'fromDate': today.format(),
                   'toDate': day_after_tomorrow.format()}

        self.get_options_chain(payload=payload)

    def test_order(self):

        payload = {enums.OrderPayload.session.value: enums.SessionOptions.NORMAL.value,
                   enums.OrderPayload.orderType.value: enums.OrderTypeOptions.LIMIT.value,
                   enums.OrderPayload.price.value: 1.,
                   enums.OrderPayload.duration.value: enums.DurationOptions.DAY.value,
                   enums.OrderPayload.quantity.value: 1,
                   enums.OrderPayload.orderLegCollection.value: [
                       {enums.OrderLegCollectionDict.instruction.value: enums.InstructionOptions.BUY_TO_OPEN.value,
                        enums.OrderLegCollectionDict.quantity.value: 1,
                        enums.OrderLegCollectionDict.instrument.value: {
                            enums.InstrumentType.symbol.value: 'SPY_041320P274',
                            enums.InstrumentType.assetType.value: enums.AssetTypeOptions.OPTION.value
                        }

                        }],
                   enums.OrderPayload.orderStrategyType.value: enums.OrderStrategyTypeOptions.SINGLE.value}

        self.place_order(payload=payload)


if __name__ == "__main__":
    utility_instance = UtilityClass()
    utility_instance.login()
    # utility_instance.get_account()
    # utility_instance.test_options_chain()
