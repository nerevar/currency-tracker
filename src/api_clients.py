from datetime import datetime, timezone, timedelta
import requests
import logging


class BaseAPIClient:
    def __init__(self):
        self.name = type(self).__name__
        self.logger = logging.getLogger(self.name)
        self.msk_offset = timedelta(hours=3)  # MSK = UTC+3

    def parse_timestamp(self, ts):
        """Конвертирует разные форматы времени в (ISO строка MSK, Unix timestamp MSK)"""
        try:
            dt_utc = None

            # Обработка числовых timestamp (секунды/миллисекунды)
            if isinstance(ts, (int, float)):
                if ts > 1e12:  # Миллисекунды
                    ts_seconds = ts / 1000
                else:  # Секунды
                    ts_seconds = ts
                dt_utc = datetime.fromtimestamp(ts_seconds, tz=timezone.utc)

            # Обработка строковых форматов
            elif isinstance(ts, str):
                ts_clean = ts.rstrip('Z').replace('Z', '')
                dt = datetime.fromisoformat(ts_clean)

                if dt.tzinfo:  # Конвертируем в UTC если есть смещение
                    dt_utc = dt.astimezone(timezone.utc)
                else:  # Предполагаем UTC если нет информации
                    dt_utc = dt.replace(tzinfo=timezone.utc)

            else:
                raise ValueError(f"Unsupported timestamp type: {type(ts)}")

            # Конвертация в московское время (UTC+3)
            dt_msk = dt_utc + self.msk_offset

            # Форматируем результат
            iso_msk = dt_msk.isoformat(timespec='milliseconds') + '+03:00'
            unix_msk = int(dt_utc.timestamp())

            return iso_msk, unix_msk

        except Exception as e:
            self.logger.error(f"Timestamp parse error: {e}")
            now = datetime.now(timezone.utc) + self.msk_offset
            return now.isoformat(timespec='milliseconds') + '+03:00', int(now.timestamp())

class ArdshinbankClient(BaseAPIClient):
    API_URL = 'https://website-api.ardshinbank.am/currency'

    def parse_rate(self, data, currency, operation_type):
        try:
            value = float(next(x for x in data['data']['currencies']['no_cash'] if x['type'] == currency)[operation_type])
            return value
        except Exception as e:
            self.logger.error(f"Arshinbank get rate for {currency} {operation_type}: {e}")
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
                'timestamp': self.parse_timestamp(data['updatedAt'])
            }
        except Exception as e:
            self.logger.error(f'{self.name} error: {e}')
            return None

class TinkoffClient(BaseAPIClient):
    API_URL_USD = 'https://api.tinkoff.ru/v1/currency_rates?from=USD&to=RUB'
    API_URL_CNY = 'https://api.tinkoff.ru/v1/currency_rates?from=CNY&to=RUB'

    def parse_rate(self, data):
        try:
            value = next((x for x in data['payload']['rates'] if x['category'] == 'DebitCardsTransfers'))['sell']
            return value
        except Exception as e:
            self.logger.error(f"Tinkoff get rate error for {data}: {e}")
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
                'timestamp': self.parse_timestamp(usd_data['payload']['lastUpdate']['milliseconds'])
            }
        except Exception as e:
            self.logger.error(f"Tinkoff error: {e}")
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
                'timestamp': self.parse_timestamp(data['Date'])
            }
        except Exception as e:
            self.logger.error(f"CBR error: {e}")
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
                'timestamp': self.parse_timestamp(usd_data['time_last_updated'])
            }
        except Exception as e:
            self.logger.error(f"Forex error: {e}")
            return None