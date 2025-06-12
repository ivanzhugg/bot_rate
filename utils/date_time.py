import datetime
def get_current_date_time():
    """
    Возвращает текущие дату и время в формате строки:
    - дата: YYYY-MM-DD
    - время: HH:MM:SS

    Пример использования:
        date_str, time_str = get_current_date_time()
    """
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    return date_str, time_str
