import requests
from bs4 import BeautifulSoup
import re

def get_cashe():
    session = requests.Session()
    resp = session.get("https://strl-x-chng.com/exchange-CASHRUB-to-USDTTRC20/")
    html = resp.text
    match = re.search(r'yid=([0-9a-f]+)', html)
    yid = match.group(1)
    ajax_url = (
        "https://strl-x-chng.com/premium_site_action-exchange_calculator.html"
        f"?meth=post&yid={yid}&ynd=0&lang=ru"
    )
    data = {
        "id":  "1465",           # id обмена
        "sum": "81.4215",        # сумма, по которой считаем
        "dej": "1",              # направление (1 – из первой валюты во вторую)
        "cd":  "sd=1&city=KRSK"  # дополнительные параметры (город и т. п.)
    }
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.0.0 Safari/537.36"
        ),
        "Referer": "https://strl-x-chng.com/exchange-CASHRUB-to-USDTTRC20/"
    }
    response = session.post(ajax_url, data=data, headers=headers)
    a = re.search(r'"course_html":"([0-9\.]+)', response.text).group(1)
    return float(a)
