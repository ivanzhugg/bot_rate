import requests
import pandas as pd

API_KEY = "AIzaSyAvQeJrjigxhtO-s7mJWyLnVQCmxoJhyOg"
SPREADSHEET_ID = "1ITNGqzhTEjfEyFgV8lM3V7sDE965WjmXWNZPgGHcHuc"

def list_sheet_titles(spreadsheet_id: str, api_key: str) -> list:
    """Вернёт названия всех листов в таблице."""
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{spreadsheet_id}?fields=sheets.properties.title&key={api_key}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    sheets = resp.json().get("sheets", [])
    return [s["properties"]["title"] for s in sheets]

def fetch_values(spreadsheet_id: str, api_key: str, sheet_title: str) -> list:
    """Вернёт массив строк (values) из запрошенного листа."""
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/"
        f"{spreadsheet_id}/values/{sheet_title}?key={api_key}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json().get("values", [])

def get_rate():
    # 1) Узнаём реальные названия листов
    titles = list_sheet_titles(SPREADSHEET_ID, API_KEY)
    if not titles:
        raise SystemExit("Не удалось найти ни одного листа.")
    sheet = titles[0]  # или укажите явно, если он не первый

    # 2) Загружаем все значения
    values = fetch_values(SPREADSHEET_ID, API_KEY, sheet)
    if not values or len(values) < 2:
        raise SystemExit("Нет заголовков или данных в листе.")

    # 3) Собираем DataFrame
    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers)

    # 4) Достаём конкретные ячейки по названиям колонок
    #    Предполагаем, что нужные значения в первой строке данных (индекс 0)
    sbp_value = df.loc[0, "сбп"]
    yuan_value = df.loc[0, "юань"]

    return list(map(int, [sbp_value, yuan_value]))
    
