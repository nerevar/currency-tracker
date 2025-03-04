import csv
import sqlite3
from datetime import datetime
from pathlib import Path


class DataHandler:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def save_to_sql(self, data):
        conn = sqlite3.connect(self.data_dir/"rates.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS rates
            (source TEXT, currency_pair TEXT, rate REAL, iso_datetime TEXT, timestamp timestamp)""")

        for source, rates in data.items():
            if not rates: continue
            for pair, value in rates.items():
                if pair == "timestamp": continue
                c.execute("INSERT INTO rates VALUES (?,?,?,?)",
                         (source, pair, value, rates["timestamp"]))
        conn.commit()
        conn.close()

    def save_to_csv(self, data):
        month = datetime.now().strftime("%Y-%m")
        csv_file = self.data_dir/"rates"/f"{month}.csv"
        csv_file.parent.mkdir(exist_ok=True)

        fieldnames = ["source", "currency_pair", "rate", "timestamp"]
        try:
            with open(csv_file, "a") as f:
                writer = csv.DictWriter(f, fieldnames)
                if f.tell() == 0:
                    writer.writeheader()
                for source, rates in data.items():
                    if not rates: continue
                    for pair, value in rates.items():
                        if pair == "timestamp": continue
                        writer.writerow({
                            "source": source,
                            "currency_pair": pair,
                            "rate": value,
                            "timestamp": rates["timestamp"],
                        })
        except Exception as e:
            print(f"CSV save error: {e}")
