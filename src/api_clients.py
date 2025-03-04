from datetime import datetime, timedelta, timezone

import requests
from utils import parse_timestamp, get_logger


class BaseAPIClient:
    def __init__(self):
        self.name = type(self).__name__
        self.logger = get_logger(self.name)


class ArdshinbankClient(BaseAPIClient):
    API_URL = 'https://website-api.ardshinbank.am/currency'

    def parse_rate(self, data, currency, operation_type):
        try:
            value = float(
                next(x for x in data['data']['currencies']['no_cash'] if x['type'] == currency)[operation_type]
            )
            return value
        except Exception as e:
            self.logger.error(f'Arshinbank get rate for {currency} {operation_type}: {e}')
            return None

    def get_rates(self):
        try:
            self.logger.info(f'make request {self.API_URL}')
            response = requests.get(self.API_URL)
            data = response.json()

            RUR_buy = self.parse_rate(data, 'RUR', 'buy')
            USD_sell = self.parse_rate(data, 'USD', 'sell')
            CNY_sell = self.parse_rate(data, 'CNY', 'sell')
            if not RUR_buy:
                return None

            return {
                'USD/RUB': USD_sell / RUR_buy,
                'CNY/RUB': CNY_sell / RUR_buy,
                'iso_datetime': parse_timestamp(data['updatedAt']),
            }
        except Exception as e:
            self.logger.error(f'{self.name} error: {e}')
            return None


class TinkoffClient(BaseAPIClient):
    API_URL_USD = 'https://api.tinkoff.ru/v1/currency_rates?from=USD&to=RUB'
    API_URL_CNY = 'https://api.tinkoff.ru/v1/currency_rates?from=CNY&to=RUB'

    def parse_rate(self, data):
        try:
            value = next(x for x in data['payload']['rates'] if x['category'] == 'DebitCardsTransfers')['sell']
            return value
        except Exception as e:
            self.logger.error(f'Tinkoff get rate error for {data}: {e}')
            return None

    def get_rates(self):
        try:
            self.logger.info(f'make request {self.API_URL_USD}')
            usd_data = requests.get(self.API_URL_USD).json()
            usd_sell = self.parse_rate(usd_data)

            self.logger.info(f'make request {self.API_URL_CNY}')
            cny_data = requests.get(self.API_URL_CNY).json()
            cny_sell = self.parse_rate(cny_data)

            return {
                'USD/RUB': usd_sell,
                'CNY/RUB': cny_sell,
                'iso_datetime': parse_timestamp(usd_data['payload']['lastUpdate']['milliseconds']),
            }
        except Exception as e:
            self.logger.error(f'Tinkoff error: {e}')
            return None


class CBRClient(BaseAPIClient):
    API_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'

    def get_rates(self):
        try:
            self.logger.info(f'make request {self.API_URL}')
            data = requests.get(self.API_URL).json()

            return {
                'USD/RUB': data['Valute']['USD']['Value'],
                'CNY/RUB': data['Valute']['CNY']['Value'],
                'iso_datetime': parse_timestamp(data['Date']),
            }
        except Exception as e:
            self.logger.error(f'CBR error: {e}')
            return None


class ForexClient(BaseAPIClient):
    API_URL_USD = 'https://api.exchangerate-api.com/v4/latest/USD'
    API_URL_CNY = 'https://api.exchangerate-api.com/v4/latest/CNY'

    def get_rates(self):
        try:
            self.logger.info(f'make request {self.API_URL_USD}')
            usd_data = requests.get(self.API_URL_USD).json()

            self.logger.info(f'make request {self.API_URL_CNY}')
            cny_data = requests.get(self.API_URL_CNY).json()

            return {
                'USD/RUB': usd_data['rates']['RUB'],
                'CNY/RUB': cny_data['rates']['RUB'],
                'iso_datetime': parse_timestamp(usd_data['time_last_updated']),
            }
        except Exception as e:
            self.logger.error(f'Forex error: {e}')
            return None
