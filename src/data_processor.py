import csv
import sqlite3
from datetime import datetime
from pathlib import Path

from utils import get_logger


class DataHandler:
    def __init__(self):
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        self.logger = get_logger(__name__)

    def save_to_sql(self, data):
        conn = sqlite3.connect(self.data_dir / 'rates.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS rates
            (source TEXT, currency_pair TEXT, rate REAL, iso_datetime TEXT, date TEXT, timestamp timestamp)""")

        for source, rates in data.items():
            if not rates:
                continue
            for pair, value in rates.items():
                if '/RUB' not in pair:
                    continue
                dt = datetime.fromisoformat(rates['iso_datetime'])
                date = dt.strftime('%Y-%m-%d')
                ts = int(dt.timestamp())
                c.execute(
                    'INSERT INTO rates VALUES (?,?,?,?,?,?)',
                    (source, pair, value, rates['iso_datetime'], date, ts),
                )
        conn.commit()
        conn.close()
        self.logger.info('SQL INSERT DONE')

    def save_to_csv(self, data):
        month = datetime.now().strftime('%Y-%m')
        csv_file = self.data_dir / 'rates' / f'{month}.csv'
        csv_file.parent.mkdir(exist_ok=True)

        fieldnames = ['source', 'currency_pair', 'rate', 'iso_datetime', 'date', 'timestamp']
        try:
            with open(csv_file, 'a') as f:
                writer = csv.DictWriter(f, fieldnames)
                if f.tell() == 0:
                    writer.writeheader()
                for source, rates in data.items():
                    if not rates:
                        continue
                    for pair, value in rates.items():
                        if '/RUB' not in pair:
                            continue
                        dt = datetime.fromisoformat(rates['iso_datetime'])
                        date = dt.strftime('%Y-%m-%d')
                        ts = int(dt.timestamp())
                        writer.writerow(
                            {
                                'source': source,
                                'currency_pair': pair,
                                'rate': value,
                                'iso_datetime': rates['iso_datetime'],
                                'date': date,
                                'timestamp': ts,
                            }
                        )
            self.logger.info(f'CSV update successful: {csv_file}')
        except Exception as e:
            print(f'CSV save error: {e}')
