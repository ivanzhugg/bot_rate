import mysql.connector
from mysql.connector import Error


def get_connection(host: str, user: str, password: str, database: str):
    """
    Создает и возвращает подключение к базе данных.
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            port=3306,
            user=user,
            password=password,
            database=database
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def add_service(
    conn,
    operation_type: str,
    quantity: str,
    cny: float,
    city: str,
    full_name: str,
    tg_id: int,
    username: str,
    date_of_request: str,
    time_of_request: str,
    desired_time: str
) -> bool:
    """
    Добавляет запись в таблицу service.
    Возвращает True при успехе, False при ошибке.
    """
    sql = (
        "INSERT INTO service "
        "(operation_type, quantity, city, cny, full_name, "
        " tg_id, username, date_of_request, time_of_request, desired_time) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    params = (
        operation_type,
        quantity,
        city,
        cny,
        full_name,
        tg_id,
        username,
        date_of_request,
        time_of_request,
        desired_time
    )
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error adding service: {e}")
        return False


def add_request(
    conn,
    tg_id: int,
    date: str,
    time: str,
    operation_type: str
) -> bool:
    """
    Добавляет запись в таблицу request.
    Возвращает True при успехе, False при ошибке.
    """
    sql = (
        "INSERT INTO request (tg_id, date, time, operation_type) "
        "VALUES (%s, %s, %s, %s)"
    )
    params = (tg_id, date, time, operation_type)
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error adding request: {e}")
        return False


def get_all_courses(conn) -> list:
    """
    Возвращает список всех записей из таблицы courses.
    Каждый элемент списка — кортеж (admin_tg, sbp_rate, CNY_rate).
    """
    sql = "SELECT admin_tg, sbp_rate, CNY_rate FROM courses"
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Error as e:
        print(f"Error fetching courses: {e}")
        return []


