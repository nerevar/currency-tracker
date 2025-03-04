from datetime import datetime, timedelta, timezone

import dateutil.parser


def parse_timestamp(input_data):
    # Московское время (UTC+3)
    moscow_tz = timezone(timedelta(hours=3))

    # Если входные данные - это число (int или float), то это Unix timestamp или timestamp в миллисекундах
    if isinstance(input_data, (int, float)):
        # Если число слишком велико, предположим, что это миллисекунды
        if input_data > 1e10:
            input_data /= 1000
        timestamp = input_data
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    # Если входные данные - это строка, попытаемся распарсить её как дату
    elif isinstance(input_data, str):
        # Пытаемся использовать dateutil для разбора строки
        try:
            dt = dateutil.parser.isoparse(input_data)
            timestamp = dt.timestamp()
        except (ValueError, OverflowError):
            raise ValueError('Unknown date format')
    else:
        raise ValueError('Unsupported input type')

    # Конвертируем время в московское
    moscow_time = dt.astimezone(moscow_tz)

    # Форматируем время в ISO формате
    iso_datetime = moscow_time.isoformat()

    # Возвращаем результат
    return iso_datetime, int(timestamp)
