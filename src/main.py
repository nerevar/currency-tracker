import os
from api_clients import (
    ArdshinbankClient,
    TinkoffClient,
    CBRClient,
    ForexClient,
    CashRBCClient,
    BestChangeClient,
)
from data_processor import DataHandler
import argparse


def parse_args():
    """
    Парсинг аргументов командной строки.

    Возвращает:
        argparse.Namespace: Объект с разобранными аргументами командной строки
    """
    parser = argparse.ArgumentParser(description='Получение и обработка курсов валют из различных источников')

    parser.add_argument('-v', '--verbose', action='store_true', help='Вывести полученные данные')

    parser.add_argument(
        '-c',
        '--client',
        action='append',
        choices=['ardshinbank', 'tinkoff', 'cbr', 'forex', 'rbc_cash', 'bestchange'],
        help='Список клиентов для получения данных (можно указать несколько раз). Если не указано, используются все клиенты',
    )

    parser.add_argument('-ns', '--no-sql', action='store_true', help='Не сохранять данные в SQL базу')

    parser.add_argument('-nf', '--no-file', action='store_true', help='Не сохранять данные в CSV файл')

    parser.add_argument(
        '-nd',
        '--no-data',
        action='store_true',
        help='Не сохранять данные вообще (приоритетнее других флагов сохранения)',
    )

    return parser.parse_args()


def main():
    # Парсинг аргументов командной строки
    args = parse_args()

    BESTCHANGE_API_KEY = os.getenv('BESTCHANGE_API_KEY')

    # Инициализация клиентов
    all_clients = {
        'ardshinbank': ArdshinbankClient(),
        'tinkoff': TinkoffClient(),
        'cbr': CBRClient(),
        'forex': ForexClient(),
        'rbc_cash': CashRBCClient(),
        'bestchange': BestChangeClient(BESTCHANGE_API_KEY),
    }

    # Определение списка используемых клиентов
    clients = {}
    if args.client:
        # Если указан список клиентов - используем только их
        for client_name in args.client:
            clients[client_name] = all_clients[client_name]
    else:
        # Иначе используем все доступные клиенты
        clients = all_clients

    # Получение данных
    data = {}
    for name, client in clients.items():
        data[name] = client.get_rates()

    # Вывод данных, если указан флаг verbose
    if args.verbose:
        print(data)

    # Сохранение данных
    if not args.no_data:
        handler = DataHandler()

        # Сохранение в SQL, если не указан флаг no-sql
        if not args.no_sql:
            handler.save_to_sql(data)

        # Сохранение в CSV, если не указан флаг no-file
        if not args.no_file:
            handler.save_to_csv(data)


if __name__ == '__main__':
    main()
