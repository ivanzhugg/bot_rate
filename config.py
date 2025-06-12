import os
from dotenv import load_dotenv

load_dotenv(override=True)  # читает .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH=os.getenv("DB_PATH")
DB_LOGIN=os.getenv("DB_LOGIN")
DB_PASS=os.getenv("DB_PASS")
DB_NAME=os.getenv("DB_NAME")

