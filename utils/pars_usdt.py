import requests
from bs4 import BeautifulSoup
import re
def get_usdt():
  session = requests.Session()
  resp = session.get("https://grinex.io/rates?offset=0")
  html = resp.text
  match = re.search(r'usdtrub":\{"sell":"([0-9\.]+)"', html)
  return float(match.group(1))
