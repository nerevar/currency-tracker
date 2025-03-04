import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from copy import deepcopy

from utils import get_logger


class DataHandler:
    def __init__(self):
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        self.logger = get_logger(__name__)

    def extract_rates(self, rates):
        results = []
        for pair, value in rates.items():
            if '/RUB' not in pair or not isinstance(value, dict):
                continue

            dt = datetime.fromisoformat(rates['iso_datetime'])
            result = {
                'currency_pair': pair,
                'iso_datetime': rates['iso_datetime'],
                'date': dt.strftime('%Y-%m-%d'),
                'timestamp': int(dt.timestamp()),
            }
            for rate_type, rate in value.items():
                current_result = deepcopy(result)
                current_result['rate'] = rate
                current_result['rate_type'] = rate_type
                results.append(current_result)
        return results

    def save_to_sql(self, data):
        conn = sqlite3.connect(self.data_dir / 'rates.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS rates (
            source TEXT,
            currency_pair TEXT,
            rate REAL,
            rate_type TEXT,
            iso_datetime TEXT,
            date TEXT,
            timestamp timestamp
        )""")

        for source, rates in data.items():
            if not rates:
                continue
            results = self.extract_rates(rates)
            for result in results:
                c.execute(
                    'INSERT INTO rates VALUES (?,?,?,?,?,?,?)',
                    (
                        source,
                        result['currency_pair'],
                        result['rate'],
                        result['rate_type'],
                        result['iso_datetime'],
                        result['date'],
                        result['timestamp'],
                    ),
                )
        conn.commit()
        conn.close()
        self.logger.info('SQL INSERT DONE')

    def save_to_csv(self, data):
        month = datetime.now().strftime('%Y-%m')
        csv_file = self.data_dir / 'rates' / f'{month}.csv'
        csv_file.parent.mkdir(exist_ok=True)

        fieldnames = ['source', 'currency_pair', 'rate', 'rate_type', 'iso_datetime', 'date', 'timestamp']
        try:
            with open(csv_file, 'a') as f:
                writer = csv.DictWriter(f, fieldnames)
                if f.tell() == 0:
                    writer.writeheader()
                for source, rates in data.items():
                    if not rates:
                        continue
                    results = self.extract_rates(rates)
                    for result in results:
                        writer.writerow({
                            'source': source,
                            'currency_pair': result['currency_pair'],
                            'rate': result['rate'],
                            'rate_type': result['rate_type'],
                            'iso_datetime': result['iso_datetime'],
                            'date': result['date'],
                            'timestamp': result['timestamp'],
                        })
            self.logger.info(f'CSV update successful: {csv_file}')
        except Exception as e:
            print(f'CSV save error: {e}')
