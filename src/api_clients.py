import time

import requests
from utils import parse_timestamp, get_logger
from metrics import MetricsCalculator


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

class CashRBCClient(BaseAPIClient):
    API_URL_USD = 'https://cash.rbc.ru/cash/json/cash_rates/?city=1&currency=3&deal=buy&amount=100'
    API_URL_CNY = 'https://cash.rbc.ru/cash/json/cash_rates/?city=1&currency=423&deal=buy&amount=100'

    def parse_rate(self, data):
        rates = []
        try:
            for item in data['banks']:
                if not item['rate'].get('sell'):
                    continue
                rates.append(float(item['rate']['sell']))
        except Exception as e:
            self.logger.error(f'Cash RBC get rate error for {data}: {e}')
        return sorted(rates)

    def get_rates(self):
        try:
            self.logger.info(f'make request {self.API_URL_USD}')
            usd_data = requests.get(self.API_URL_USD).json()
            usd_rates = self.parse_rate(usd_data)
            usd_metrics = MetricsCalculator(usd_rates)

            self.logger.info(f'make request {self.API_URL_CNY}')
            cny_data = requests.get(self.API_URL_CNY).json()
            cny_rates = self.parse_rate(cny_data)
            cny_metrics = MetricsCalculator(cny_rates)

            return {
                'USD/RUB min': usd_metrics.calc_min(),
                'USD/RUB p05': usd_metrics.calc_p05(),
                'USD/RUB median': usd_metrics.calc_median(),
                'CNY/RUB min': cny_metrics.calc_min(),
                'CNY/RUB p05': cny_metrics.calc_p05(),
                'CNY/RUB median': cny_metrics.calc_median(),
                'iso_datetime': parse_timestamp(int(time.time())),
            }
        except Exception as e:
            self.logger.error(f'Forex error: {e}')
            return None
