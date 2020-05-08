import numpy as np
import h5py
import os

test_file_path = 'test_file.hdf5'
if os.path.isfile(test_file_path):
    os.remove(test_file_path)
    test_file = h5py.File(test_file_path)
else:
    test_file = h5py.File(test_file_path)

test_chain_quote = {'symbol': 'SPY', 'status': 'SUCCESS',
                    'underlying': {'symbol': 'SPY', 'description': 'SPDR S&P 500', 'change': 5.08,
                                   'percentChange': 1.79, 'close': 284.25, 'quoteTime': 1588867939013,
                                   'tradeTime': 1588867937458, 'bid': 289.33, 'ask': 289.34, 'last': 289.33,
                                   'mark': 289.33, 'markChange': 5.08, 'markPercentChange': 1.79, 'bidSize': 300,
                                   'askSize': 900, 'highPrice': 289.78, 'lowPrice': 287.22, 'openPrice': 287.75,
                                   'totalVolume': 34728523, 'exchangeName': 'PAC', 'fiftyTwoWeekHigh': 339.08,
                                   'fiftyTwoWeekLow': 218.26, 'delayed': False}, 'strategy': 'SINGLE', 'interval': 0.0,
                    'isDelayed': False, 'isIndex': False, 'interestRate': 0.11, 'underlyingPrice': 289.335,
                    'volatility': 29.0, 'daysToExpiration': 0.0, 'numberOfContracts': 20, 'putExpDateMap': {
        '2020-05-08:1': {'280.0': [
            {'putCall': 'PUT',
             'symbol': 'SPY_050820P280',
             'description': 'SPY May 8 2020 280 Put (Weekly)',
             'exchangeName': 'OPR',
             'bid': 0.19,
             'ask': 0.2,
             'last': 0.19,
             'mark': 0.2,
             'bidSize': 2197,
             'askSize': 3670,
             'bidAskSize': '2197X3670',
             'lastSize': 0,
             'highPrice': 0.4,
             'lowPrice': 0.18,
             'openPrice': 0.0,
             'closePrice': 1.45,
             'totalVolume': 33814,
             'tradeDate': None,
             'tradeTimeInLong': 1588867937537,
             'quoteTimeInLong': 1588867938236,
             'netChange': -1.26,
             'volatility': 29.929,
             'delta': -0.068,
             'gamma': 0.021,
             'theta': -0.212,
             'vega': 0.028,
             'rho': -0.001,
             'openInterest': 45416,
             'timeValue': 0.19,
             'theoreticalOptionValue': 0.195,
             'theoreticalVolatility': 29.0,
             'optionDeliverablesList': None,
             'strikePrice': 280.0,
             'expirationDate': 1588968000000,
             'daysToExpiration': 1,
             'expirationType': 'S',
             'lastTradingDay': 1588982400000,
             'multiplier': 100.0,
             'settlementType': ' ',
             'deliverableNote': '',
             'isIndexOption': None,
             'percentChange': -86.9,
             'markChange': -1.26,
             'markPercentChange': -86.55,
             'nonStandard': False,
             'inTheMoney': False,
             'mini': False}],
            '281.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P281', 'description': 'SPY May 8 2020 281 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 0.25, 'ask': 0.26, 'last': 0.26, 'mark': 0.26, 'bidSize': 3305,
                 'askSize': 414, 'bidAskSize': '3305X414', 'lastSize': 0, 'highPrice': 0.58, 'lowPrice': 0.23,
                 'openPrice': 0.0, 'closePrice': 1.73, 'totalVolume': 8809, 'tradeDate': None,
                 'tradeTimeInLong': 1588867925281, 'quoteTimeInLong': 1588867939015, 'netChange': -1.47,
                 'volatility': 29.258, 'delta': -0.088, 'gamma': 0.025, 'theta': -0.25, 'vega': 0.034, 'rho': -0.001,
                 'openInterest': 8600, 'timeValue': 0.26, 'theoreticalOptionValue': 0.255,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 281.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -84.97,
                 'markChange': -1.48, 'markPercentChange': -85.26, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '282.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P282', 'description': 'SPY May 8 2020 282 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 0.34, 'ask': 0.35, 'last': 0.34, 'mark': 0.35, 'bidSize': 131,
                 'askSize': 2955, 'bidAskSize': '131X2955', 'lastSize': 0, 'highPrice': 0.62, 'lowPrice': 0.3,
                 'openPrice': 0.0, 'closePrice': 2.07, 'totalVolume': 11841, 'tradeDate': None,
                 'tradeTimeInLong': 1588867887829, 'quoteTimeInLong': 1588867938783, 'netChange': -1.73,
                 'volatility': 28.886, 'delta': -0.114, 'gamma': 0.031, 'theta': -0.299, 'vega': 0.041, 'rho': -0.002,
                 'openInterest': 11578, 'timeValue': 0.34, 'theoreticalOptionValue': 0.345,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 282.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -83.57,
                 'markChange': -1.72, 'markPercentChange': -83.33, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '283.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P283', 'description': 'SPY May 8 2020 283 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 0.45, 'ask': 0.46, 'last': 0.44, 'mark': 0.46, 'bidSize': 100,
                 'askSize': 2510, 'bidAskSize': '100X2510', 'lastSize': 0, 'highPrice': 0.8, 'lowPrice': 0.4,
                 'openPrice': 0.0, 'closePrice': 2.44, 'totalVolume': 27363, 'tradeDate': None,
                 'tradeTimeInLong': 1588867913706, 'quoteTimeInLong': 1588867938603, 'netChange': -2.01,
                 'volatility': 28.371, 'delta': -0.145, 'gamma': 0.037, 'theta': -0.348, 'vega': 0.049, 'rho': -0.002,
                 'openInterest': 10305, 'timeValue': 0.44, 'theoreticalOptionValue': 0.455,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 283.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -82.0,
                 'markChange': -1.99, 'markPercentChange': -81.39, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '284.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P284', 'description': 'SPY May 8 2020 284 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 0.58, 'ask': 0.59, 'last': 0.59, 'mark': 0.59, 'bidSize': 979,
                 'askSize': 651, 'bidAskSize': '979X651', 'lastSize': 0, 'highPrice': 1.03, 'lowPrice': 0.52,
                 'openPrice': 0.0, 'closePrice': 2.87, 'totalVolume': 16784, 'tradeDate': None,
                 'tradeTimeInLong': 1588867897731, 'quoteTimeInLong': 1588867938940, 'netChange': -2.28,
                 'volatility': 27.666, 'delta': -0.18, 'gamma': 0.044, 'theta': -0.392, 'vega': 0.056, 'rho': -0.003,
                 'openInterest': 7821, 'timeValue': 0.59, 'theoreticalOptionValue': 0.585,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 284.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -79.42,
                 'markChange': -2.28, 'markPercentChange': -79.59, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '285.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P285', 'description': 'SPY May 8 2020 285 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 0.75, 'ask': 0.77, 'last': 0.75, 'mark': 0.76, 'bidSize': 567,
                 'askSize': 969, 'bidAskSize': '567X969', 'lastSize': 0, 'highPrice': 1.31, 'lowPrice': 0.68,
                 'openPrice': 0.0, 'closePrice': 3.37, 'totalVolume': 50557, 'tradeDate': None,
                 'tradeTimeInLong': 1588867933781, 'quoteTimeInLong': 1588867938930, 'netChange': -2.62,
                 'volatility': 27.125, 'delta': -0.225, 'gamma': 0.052, 'theta': -0.438, 'vega': 0.064, 'rho': -0.004,
                 'openInterest': 28374, 'timeValue': 0.75, 'theoreticalOptionValue': 0.76,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 285.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -77.74,
                 'markChange': -2.61, 'markPercentChange': -77.45, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '286.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P286', 'description': 'SPY May 8 2020 286 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 0.97, 'ask': 0.98, 'last': 0.98, 'mark': 0.98, 'bidSize': 118,
                 'askSize': 310, 'bidAskSize': '118X310', 'lastSize': 0, 'highPrice': 1.64, 'lowPrice': 0.87,
                 'openPrice': 0.0, 'closePrice': 3.92, 'totalVolume': 25928, 'tradeDate': None,
                 'tradeTimeInLong': 1588867923574, 'quoteTimeInLong': 1588867938695, 'netChange': -2.94,
                 'volatility': 26.523, 'delta': -0.276, 'gamma': 0.059, 'theta': -0.478, 'vega': 0.072, 'rho': -0.004,
                 'openInterest': 11801, 'timeValue': 0.98, 'theoreticalOptionValue': 0.975,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 286.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -75.01,
                 'markChange': -2.95, 'markPercentChange': -75.14, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '287.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P287', 'description': 'SPY May 8 2020 287 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 1.23, 'ask': 1.24, 'last': 1.22, 'mark': 1.23, 'bidSize': 134,
                 'askSize': 117, 'bidAskSize': '134X117', 'lastSize': 0, 'highPrice': 2.04, 'lowPrice': 1.12,
                 'openPrice': 0.0, 'closePrice': 4.55, 'totalVolume': 43876, 'tradeDate': None,
                 'tradeTimeInLong': 1588867932310, 'quoteTimeInLong': 1588867938479, 'netChange': -3.33,
                 'volatility': 25.838, 'delta': -0.334, 'gamma': 0.066, 'theta': -0.508, 'vega': 0.078, 'rho': -0.005,
                 'openInterest': 13799, 'timeValue': 1.22, 'theoreticalOptionValue': 1.235,
                 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 287.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -73.17,
                 'markChange': -3.31, 'markPercentChange': -72.84, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '288.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P288', 'description': 'SPY May 8 2020 288 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 1.55, 'ask': 1.56, 'last': 1.55, 'mark': 1.56, 'bidSize': 129,
                 'askSize': 28,
                 'bidAskSize': '129X28', 'lastSize': 0, 'highPrice': 2.52, 'lowPrice': 1.41, 'openPrice': 0.0,
                 'closePrice': 5.23, 'totalVolume': 52210, 'tradeDate': None, 'tradeTimeInLong': 1588867913706,
                 'quoteTimeInLong': 1588867938404, 'netChange': -3.68, 'volatility': 25.168, 'delta': -0.4,
                 'gamma': 0.072,
                 'theta': -0.527, 'vega': 0.083, 'rho': -0.006, 'openInterest': 8541, 'timeValue': 1.55,
                 'theoreticalOptionValue': 1.555, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 288.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -70.35, 'markChange': -3.67, 'markPercentChange': -70.25,
                 'nonStandard': False, 'inTheMoney': False, 'mini': False}], '289.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P289', 'description': 'SPY May 8 2020 289 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 1.94, 'ask': 1.96, 'last': 1.94, 'mark': 1.95, 'bidSize': 115,
                 'askSize': 165, 'bidAskSize': '115X165', 'lastSize': 0, 'highPrice': 3.06, 'lowPrice': 1.78,
                 'openPrice': 0.0, 'closePrice': 5.99, 'totalVolume': 24461, 'tradeDate': None,
                 'tradeTimeInLong': 1588867935075, 'quoteTimeInLong': 1588867938323, 'netChange': -4.05,
                 'volatility': 24.59, 'delta': -0.473, 'gamma': 0.076, 'theta': -0.531, 'vega': 0.085, 'rho': -0.008,
                 'openInterest': 6920, 'timeValue': 1.94, 'theoreticalOptionValue': 1.95, 'theoreticalVolatility': 29.0,
                 'optionDeliverablesList': None, 'strikePrice': 289.0, 'expirationDate': 1588968000000,
                 'daysToExpiration': 1, 'expirationType': 'S', 'lastTradingDay': 1588982400000, 'multiplier': 100.0,
                 'settlementType': ' ', 'deliverableNote': '', 'isIndexOption': None, 'percentChange': -67.6,
                 'markChange': -4.04, 'markPercentChange': -67.43, 'nonStandard': False, 'inTheMoney': False,
                 'mini': False}], '290.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P290', 'description': 'SPY May 8 2020 290 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 2.41, 'ask': 2.43, 'last': 2.38, 'mark': 2.42, 'bidSize': 62,
                 'askSize': 151,
                 'bidAskSize': '62X151', 'lastSize': 0, 'highPrice': 3.7, 'lowPrice': 2.21, 'openPrice': 0.0,
                 'closePrice': 6.79, 'totalVolume': 30407, 'tradeDate': None, 'tradeTimeInLong': 1588867929188,
                 'quoteTimeInLong': 1588867938347, 'netChange': -4.41, 'volatility': 24.02, 'delta': -0.55,
                 'gamma': 0.077,
                 'theta': -0.517, 'vega': 0.085, 'rho': -0.009, 'openInterest': 11046, 'timeValue': 1.71,
                 'theoreticalOptionValue': 2.42, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 290.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -64.93, 'markChange': -4.37, 'markPercentChange': -64.34,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '291.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P291', 'description': 'SPY May 8 2020 291 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 2.96, 'ask': 2.98, 'last': 2.97, 'mark': 2.97, 'bidSize': 18,
                 'askSize': 100,
                 'bidAskSize': '18X100', 'lastSize': 0, 'highPrice': 4.41, 'lowPrice': 2.7, 'openPrice': 0.0,
                 'closePrice': 7.64, 'totalVolume': 4730, 'tradeDate': None, 'tradeTimeInLong': 1588867893950,
                 'quoteTimeInLong': 1588867938404, 'netChange': -4.67, 'volatility': 23.465, 'delta': -0.628,
                 'gamma': 0.075, 'theta': -0.484, 'vega': 0.081, 'rho': -0.01, 'openInterest': 4976, 'timeValue': 1.3,
                 'theoreticalOptionValue': 2.97, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 291.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -61.14, 'markChange': -4.67, 'markPercentChange': -61.14,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '292.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P292', 'description': 'SPY May 8 2020 292 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 3.58, 'ask': 3.61, 'last': 3.65, 'mark': 3.6, 'bidSize': 100,
                 'askSize': 35,
                 'bidAskSize': '100X35', 'lastSize': 0, 'highPrice': 5.14, 'lowPrice': 3.36, 'openPrice': 0.0,
                 'closePrice': 8.54, 'totalVolume': 5322, 'tradeDate': None, 'tradeTimeInLong': 1588867875782,
                 'quoteTimeInLong': 1588867938334, 'netChange': -4.89, 'volatility': 22.841, 'delta': -0.705,
                 'gamma': 0.07,
                 'theta': -0.432, 'vega': 0.074, 'rho': -0.011, 'openInterest': 3747, 'timeValue': 0.98,
                 'theoreticalOptionValue': 3.595, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 292.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -57.25, 'markChange': -4.94, 'markPercentChange': -57.89,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '293.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P293', 'description': 'SPY May 8 2020 293 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 4.29, 'ask': 4.33, 'last': 4.33, 'mark': 4.31, 'bidSize': 30,
                 'askSize': 25,
                 'bidAskSize': '30X25', 'lastSize': 0, 'highPrice': 5.99, 'lowPrice': 4.03, 'openPrice': 0.0,
                 'closePrice': 9.46, 'totalVolume': 970, 'tradeDate': None, 'tradeTimeInLong': 1588867463442,
                 'quoteTimeInLong': 1588867938797, 'netChange': -5.13, 'volatility': 22.385, 'delta': -0.776,
                 'gamma': 0.062, 'theta': -0.37, 'vega': 0.064, 'rho': -0.013, 'openInterest': 2146, 'timeValue': 0.66,
                 'theoreticalOptionValue': 4.31, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 293.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -54.21, 'markChange': -5.15, 'markPercentChange': -54.43,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '294.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P294', 'description': 'SPY May 8 2020 294 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 5.06, 'ask': 5.11, 'last': 5.08, 'mark': 5.09, 'bidSize': 100,
                 'askSize': 25,
                 'bidAskSize': '100X25', 'lastSize': 0, 'highPrice': 6.62, 'lowPrice': 4.79, 'openPrice': 0.0,
                 'closePrice': 10.4, 'totalVolume': 387, 'tradeDate': None, 'tradeTimeInLong': 1588867896641,
                 'quoteTimeInLong': 1588867938846, 'netChange': -5.32, 'volatility': 21.734, 'delta': -0.84,
                 'gamma': 0.052,
                 'theta': -0.296, 'vega': 0.052, 'rho': -0.014, 'openInterest': 2286, 'timeValue': 0.41,
                 'theoreticalOptionValue': 5.085, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 294.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -51.16, 'markChange': -5.32, 'markPercentChange': -51.12,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '295.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P295', 'description': 'SPY May 8 2020 295 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 5.91, 'ask': 5.96, 'last': 5.9, 'mark': 5.94, 'bidSize': 20,
                 'askSize': 100,
                 'bidAskSize': '20X100', 'lastSize': 0, 'highPrice': 7.82, 'lowPrice': 5.6, 'openPrice': 0.0,
                 'closePrice': 11.37, 'totalVolume': 2257, 'tradeDate': None, 'tradeTimeInLong': 1588867932310,
                 'quoteTimeInLong': 1588867938768, 'netChange': -5.47, 'volatility': 21.316, 'delta': -0.89,
                 'gamma': 0.041,
                 'theta': -0.227, 'vega': 0.04, 'rho': -0.014, 'openInterest': 2296, 'timeValue': 0.23,
                 'theoreticalOptionValue': 5.935, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 295.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -48.1, 'markChange': -5.43, 'markPercentChange': -47.79,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '296.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P296', 'description': 'SPY May 8 2020 296 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 6.8, 'ask': 6.84, 'last': 6.88, 'mark': 6.82, 'bidSize': 100,
                 'askSize': 1,
                 'bidAskSize': '100X1', 'lastSize': 0, 'highPrice': 8.5, 'lowPrice': 6.59, 'openPrice': 0.0,
                 'closePrice': 12.35, 'totalVolume': 237, 'tradeDate': None, 'tradeTimeInLong': 1588867513874,
                 'quoteTimeInLong': 1588867938797, 'netChange': -5.47, 'volatility': 20.405, 'delta': -0.934,
                 'gamma': 0.029, 'theta': -0.154, 'vega': 0.027, 'rho': -0.015, 'openInterest': 1182, 'timeValue': 0.21,
                 'theoreticalOptionValue': 6.82, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 296.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -44.28, 'markChange': -5.53, 'markPercentChange': -44.76,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '297.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P297', 'description': 'SPY May 8 2020 297 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 7.73, 'ask': 7.79, 'last': 7.75, 'mark': 7.76, 'bidSize': 100,
                 'askSize': 15,
                 'bidAskSize': '100X15', 'lastSize': 0, 'highPrice': 9.61, 'lowPrice': 7.4, 'openPrice': 0.0,
                 'closePrice': 13.33, 'totalVolume': 201, 'tradeDate': None, 'tradeTimeInLong': 1588867932310,
                 'quoteTimeInLong': 1588867939064, 'netChange': -5.58, 'volatility': 19.941, 'delta': -0.962,
                 'gamma': 0.019, 'theta': -0.103, 'vega': 0.018, 'rho': -0.016, 'openInterest': 662, 'timeValue': 0.08,
                 'theoreticalOptionValue': 7.76, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 297.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -41.85, 'markChange': -5.57, 'markPercentChange': -41.77,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '298.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P298', 'description': 'SPY May 8 2020 298 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 8.69, 'ask': 8.74, 'last': 8.72, 'mark': 8.72, 'bidSize': 20,
                 'askSize': 100,
                 'bidAskSize': '20X100', 'lastSize': 0, 'highPrice': 10.48, 'lowPrice': 8.55, 'openPrice': 0.0,
                 'closePrice': 14.32, 'totalVolume': 311, 'tradeDate': None, 'tradeTimeInLong': 1588866985644,
                 'quoteTimeInLong': 1588867938259, 'netChange': -5.6, 'volatility': 18.289, 'delta': -0.985,
                 'gamma': 0.009,
                 'theta': -0.051, 'vega': 0.008, 'rho': -0.016, 'openInterest': 618, 'timeValue': 0.05,
                 'theoreticalOptionValue': 8.715, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 298.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -39.09, 'markChange': -5.6, 'markPercentChange': -39.13,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}], '299.0': [
                {'putCall': 'PUT', 'symbol': 'SPY_050820P299', 'description': 'SPY May 8 2020 299 Put (Weekly)',
                 'exchangeName': 'OPR', 'bid': 9.66, 'ask': 9.72, 'last': 9.72, 'mark': 9.69, 'bidSize': 100,
                 'askSize': 10,
                 'bidAskSize': '100X10', 'lastSize': 0, 'highPrice': 11.7, 'lowPrice': 9.35, 'openPrice': 0.0,
                 'closePrice': 15.31, 'totalVolume': 456, 'tradeDate': None, 'tradeTimeInLong': 1588867734477,
                 'quoteTimeInLong': 1588867938938, 'netChange': -5.59, 'volatility': 5.0, 'delta': -1.0, 'gamma': 0.0,
                 'theta': -0.015, 'vega': 0.0, 'rho': -0.016, 'openInterest': 282, 'timeValue': 0.05,
                 'theoreticalOptionValue': 9.695, 'theoreticalVolatility': 29.0, 'optionDeliverablesList': None,
                 'strikePrice': 299.0, 'expirationDate': 1588968000000, 'daysToExpiration': 1, 'expirationType': 'S',
                 'lastTradingDay': 1588982400000, 'multiplier': 100.0, 'settlementType': ' ', 'deliverableNote': '',
                 'isIndexOption': None, 'percentChange': -36.51, 'markChange': -5.62, 'markPercentChange': -36.7,
                 'nonStandard': False, 'inTheMoney': True, 'mini': False}]}}, 'callExpDateMap': {}}


def group_creator(nested_dict: dict, group: h5py.Group):
    if type(nested_dict) is dict:
        # check if item is a dict
        for key in nested_dict.keys():
            if (type(nested_dict[key]) is list) or (type(nested_dict[key]) is dict):
                # if item contains a dict or a list, create a subroup for it and recurse
                subgroup = group.create_group(key)
                group_creator(nested_dict=nested_dict[key], group=subgroup)
            else:
                # if the item is not a list or a dict, then it must be a value
                # if type(nested_dict[key]) is in [np.]
                #print(np.dtype(type(nested_dict[key])))
                if type(nested_dict[key]) in [str, bool, type(None)]:
                    pass
                else:
                    data_type = np.float
                    group.create_dataset(key, shape=[100], dtype=data_type)
    elif type(nested_dict) is list:
        for item in nested_dict:
            # if the item is a list, then recurse with the original group for each item in the list
            # this has the effect of ignoring lists.
            group_creator(nested_dict=item, group=group)


group_creator(nested_dict=test_chain_quote, group=test_file)


def key_printer(item, num_tabs):
    tabs = ''
    for _ in range(num_tabs):
        tabs += '\t'

    if type(item) is h5py.Group or type(item) is h5py.File:
        print(tabs + item.name + ' ({})'.format(type(item)))
        for name, element in item.items():
            tabs += '\t'
            key_printer(element, num_tabs=num_tabs + 1)
    if type(item) is h5py.Dataset:
        tabs += '\t'
        print(tabs + item.name + ' ({}, {})'.format(type(item), item.dtype))

    return


# key_printer(item=test_file, num_tabs=0)

def write_nested_dict(nested_dict: dict, group: h5py.Group):
    num = 0
    if type(nested_dict) is dict:
        # check if item is a dict
        for key in nested_dict.keys():
            if (type(nested_dict[key]) is list) or (type(nested_dict[key]) is dict):
                # if item contains a dict or a list, create a subroup for it and recurse
                subgroup = group[key]
                write_nested_dict(nested_dict=nested_dict[key], group=subgroup)
            else:
                # if the item is not a list or a dict, then it must be a value
                # if type(nested_dict[key]) is in [np.]
                # print(np.dtype(type(nested_dict[key])))
                if type(nested_dict[key]) in [str, bool, type(None)]:
                    pass
                else:
                    print(float(nested_dict[key]))
                    data_type = np.float
                    group[key][num] = float(nested_dict[key])
    elif type(nested_dict) is list:
        for item in nested_dict:
            # if the item is a list, then recurse with the original group for each item in the list
            # this has the effect of ignoring lists.
            write_nested_dict(nested_dict=item, group=group)


write_nested_dict(nested_dict=test_chain_quote, group=test_file)


def value_printer(item, num_tabs):
    tabs = ''
    for _ in range(num_tabs):
        tabs += '\t'

    if type(item) is h5py.Group or type(item) is h5py.File:
        print(tabs + item.name + ' ({})'.format(type(item)))
        for name, element in item.items():
            tabs += '\t'
            value_printer(element, num_tabs=num_tabs + 1)
    if type(item) is h5py.Dataset:
        tabs += '\t'
        #print('something')
        print(tabs + item.name + ' ({}, {})'.format(type(item), item[0]))

    return


value_printer(item=test_file, num_tabs=0)

test_file.close()
