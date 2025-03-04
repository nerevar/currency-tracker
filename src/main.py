from api_clients import ArdshinbankClient, TinkoffClient, CBRClient, ForexClient
from data_processor import DataHandler
import logging

logging.basicConfig(level=logging.INFO)

def main():
    clients = {
        'ardshinbank': ArdshinbankClient(),
        'tinkoff': TinkoffClient(),
        'cbr': CBRClient(),
        'forex': ForexClient(),
    }

    data = {}
    for name, client in clients.items():
        data[name] = client.get_rates()

    handler = DataHandler()
    handler.save_to_sql(data)
    handler.save_to_csv(data)

if __name__ == "__main__":
    main()