import os
import json
import logging
from pathlib import Path
from decimal import Decimal, ROUND_DOWN
import time

import telebot
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, DB_PATH, DB_LOGIN, DB_PASS, DB_NAME
from utils.pars_cashe import get_cashe
from utils.pars_usdt import get_usdt
from utils.date_time import get_current_date_time
from utils.db import get_connection, add_service, add_request, get_all_courses
from utils.xlpars import get_rate

# Initialize database connection
conn = get_connection(DB_PATH, DB_LOGIN, DB_PASS, DB_NAME)
if not conn:
    logging.critical("Failed to connect to database. Exiting.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Load messages
load_dotenv()
MESSAGES_PATH = Path(__file__).parent / "texts" / "messages.json"
try:
    with open(MESSAGES_PATH, "r", encoding="utf-8") as f:
        MESSAGES = json.load(f)
except Exception as e:
    logging.error(f"Failed to load messages: {e}")
    MESSAGES = {}

# State storage for sequential dialogs
user_data = {}

def create_inline_keyboard(buttons):
    """Helper: build inline keyboard rows of 2 buttons"""
    kb = InlineKeyboardMarkup()
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        kb.row(*[InlineKeyboardButton(text=txt, callback_data=data) for txt, data in row])
    return kb

# /start handler
@bot.message_handler(commands=["start"])
def handle_start(message):
    text = MESSAGES.get('welcome', '')
    kb = create_inline_keyboard([
        ("Важно знать", "about"),
        ("Узнать курс", "rate"),
        ("Обменять валюту", "exchange"),
    ])
    bot.send_message(message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# About
@bot.callback_query_handler(func=lambda call: call.data == "about")
def about(call):
    text = MESSAGES.get('main_info', '')
    kb = create_inline_keyboard([("Вернуться в главное меню", "menu")])
    bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# Main menu callback
@bot.callback_query_handler(func=lambda call: call.data == "menu")
def menu(call):
    handle_start(call.message)

# Rate menu (asks for amount)
@bot.callback_query_handler(func=lambda call: call.data == "rate")
def rate(call):
    text = MESSAGES.get('rate_info', '')
    kb = create_inline_keyboard([
        ("СБП", "rate_sbp"),
        ("USDT", "rate_usdt"),
        ("Наличка", "rate_cache"),
        ("Вернуться в главное меню", "menu"),
    ])
    bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# Ask user for amount to calculate received currency
@bot.callback_query_handler(func=lambda call: call.data in ("rate_sbp", "rate_usdt", "rate_cache"))
def ask_rate_amount(call):
    tg = call.message.chat.id
    key = call.data.split('_', 1)[1]  # sbp, usdt, cache
    bot.clear_step_handler_by_chat_id(tg)
    if key == 'sbp':
        msg = bot.send_message(tg, "Введите сумму в RUB для обмена по СБП:")
    elif key == 'usdt':
        msg = bot.send_message(tg, "Введите сумму в USDT для обмена:")
    else:
        msg = bot.send_message(tg, "Введите сумму в RUB для наличного обмена:")
    bot.register_next_step_handler(msg, process_rate, key)

# Unified rate calculation
def process_rate(message, operation_key):
    tg = message.chat.id
    qty_text = message.text.strip()
    try:
        qty = float(qty_text)
    except ValueError:
        msg = bot.send_message(tg, "Введите сумму ещё раз:")
        return bot.register_next_step_handler(msg, process_rate, operation_key)

    try:
        if operation_key == 'sbp':
            result = qty / get_rate()[1]
        elif operation_key == 'usdt':
            result = (get_usdt() * 1.02 * qty) / get_rate()[1]
        else:
            result = (qty / get_cashe()) * get_usdt() / get_rate()[1]

        decimal_result = Decimal(result).quantize(Decimal("0.0001"), ROUND_DOWN)
        result_str = str(decimal_result)
        text = f"🔄 Вы получите: <b>{result_str}</b> CNY"
    except Exception:
        text = "❗️ Не удалось рассчитать сумму, попробуйте позже."

    date_str, time_str = get_current_date_time()
    add_request(conn, tg, date_str, time_str, operation_key)

    kb = create_inline_keyboard([("В меню", "menu")])
    bot.send_message(tg, text, reply_markup=kb, parse_mode="HTML")

# Exchange menu
@bot.callback_query_handler(func=lambda call: call.data == "exchange")
def exchange(call):
    text = MESSAGES.get('exchange_info', '')
    kb = create_inline_keyboard([
        ("СБП", "exchange_sbp"),
        ("USDT", "exchange_usdt"),
        ("Наличка", "exchange_cache"),
        ("Вернуться в главное меню", "menu"),
    ])
    bot.send_message(call.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# Simple SBP rate -> ask amount
@bot.callback_query_handler(func=lambda call: call.data == "sbp")
def sbp_rate(call):
    tg = call.message.chat.id
    bot.clear_step_handler_by_chat_id(tg)
    msg = bot.send_message(tg, "Введите сумму в RUB для обмена по СБП:")
    bot.register_next_step_handler(msg, process_rate, 'sbp')

# Simple USDT rate -> ask amount
@bot.callback_query_handler(func=lambda call: call.data == "usdt")
def usdt_rate(call):
    tg = call.message.chat.id
    bot.clear_step_handler_by_chat_id(tg)
    msg = bot.send_message(tg, "Введите сумму в USDT для обмена:")
    bot.register_next_step_handler(msg, process_rate, 'usdt')

# Simple cache rate -> ask amount
@bot.callback_query_handler(func=lambda call: call.data == "cache")
def cache_rate(call):
    tg = call.message.chat.id
    bot.clear_step_handler_by_chat_id(tg)
    msg = bot.send_message(tg, "Введите сумму в RUB для наличного обмена:")
    bot.register_next_step_handler(msg, process_rate, 'cache')
# EXCHANGE: SBP
@bot.callback_query_handler(func=lambda call: call.data == "exchange_sbp")
def exchange_sbp(call):
    tg = call.message.chat.id
    msg = bot.send_message(tg, "Введите сумму в RUB, используя только цифры:")
    bot.clear_step_handler_by_chat_id(tg)
    bot.register_next_step_handler(msg, process_simple_exchange, 'exchange_sbp')

# EXCHANGE: USDT
@bot.callback_query_handler(func=lambda call: call.data == "exchange_usdt")
def exchange_usdt(call):
    tg = call.message.chat.id
    msg = bot.send_message(tg, "Введите сумму в USDT, используя только цифры:")
    bot.clear_step_handler_by_chat_id(tg)
    bot.register_next_step_handler(msg, process_simple_exchange, 'exchange_usdt')

# Общая обработка простого обмена
def process_simple_exchange(message, operation_key):
    tg = message.chat.id
    qty_text = message.text.strip()
    try:
        qty = float(qty_text)
    except ValueError:
        msg = bot.send_message(tg, "Введите сумму еще раз:")
        return bot.register_next_step_handler(msg, process_simple_exchange, operation_key)
        
    if operation_key == 'exchange_sbp':
        result = qty / get_rate()[1]
    else:  # 'exchange_usdt'
        result = (get_usdt() * 1.02 * qty) / get_rate()[1]

    decimal_result = Decimal(result).quantize(Decimal("0.0001"), ROUND_DOWN)
    result_str = str(decimal_result)

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Вернуться в главное меню", callback_data="menu"),
        InlineKeyboardButton(
            "Отправить заявку",
            callback_data=f"confirm_{operation_key}:{qty_text}:{result_str}"
        )
    )

    bot.send_message(
        tg,
        f"Вы получите: {result_str} CNY\n"
        "Нажмите «Отправить заявку», чтобы подтвердить, или «Вернуться» для отмены.",
        reply_markup=kb
    )

# Confirm SBP/USDT
@bot.callback_query_handler(
    func=lambda call: call.data.startswith("confirm_exchange_sbp:") 
                   or call.data.startswith("confirm_exchange_usdt:")
)
def confirm_exchange(call):
    tg = call.message.chat.id
    _, payload = call.data.split("_", 1)
    operation_key, qty_text, result_str = payload.split(":", 2)

    try:
        cny_value = float(result_str)
    except ValueError:
        return bot.send_message(tg, "⚠️ Некорректная сумма. Начните заново.")

    username = call.from_user.username or ''
    date_str, time_str = get_current_date_time()

    add_service(
        conn,
        operation_key,
        qty_text,
        cny_value,
        '', '', tg, username, date_str, time_str, ''
    )

    admin_id = get_all_courses(conn)[0][0]
    bot.send_message(
        admin_id,
        f"Новая сделка {operation_key} от {tg} (@{username}):\n"
        f"  Введено: {qty_text}\n"
        f"  Получит: {result_str} CNY"
    )

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("В меню", callback_data="menu"))
    bot.send_message(tg, f"✅ Ваша заявка обрабатывается. Администратор: {bot.get_chat(admin_id).username}", reply_markup=kb)

# EXCHANGE: Cache
@bot.callback_query_handler(func=lambda call: call.data == "exchange_cache")
def exchange_cache(call):
    tg = call.message.chat.id
    user_data[tg] = {}
    msg = bot.send_message(tg, "Введите сумму в RUB, используя только цифры:")
    bot.clear_step_handler_by_chat_id(tg)
    bot.register_next_step_handler(msg, process_cache_amount)


def process_cache_amount(message):
    tg = message.chat.id
    qty_text = message.text.strip()
    try:
        float(qty_text)
    except ValueError:
        msg = bot.send_message(tg, "Введите сумму еще раз:")
        return bot.register_next_step_handler(msg, process_cache_amount)
        
    user_data[tg]['quantity'] = qty_text
    msg = bot.send_message(tg, "Введите ваше ФИО:")
    bot.clear_step_handler_by_chat_id(tg)
    bot.register_next_step_handler(msg, process_cache_fullname)


def process_cache_fullname(message):
    tg = message.chat.id
    user_data[tg]['full_name'] = message.text.strip()
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Использовать свой username", callback_data="use_own_username"))
    msg = bot.send_message(
        tg,
        "Укажите username для связи (или нажмите кнопку, чтобы использовать ваш Telegram username):",
        reply_markup=kb
    )
    bot.clear_step_handler_by_chat_id(tg)
    bot.register_next_step_handler(msg, process_cache_username)


def process_cache_username(message):
    tg = message.chat.id
    bot.clear_step_handler_by_chat_id(tg)
    user_data[tg]['username'] = message.text.strip()
    msg = bot.send_message(tg, "Укажите ваш город:")
    bot.register_next_step_handler(msg, process_cache_city)

@bot.callback_query_handler(func=lambda call: call.data == "use_own_username")
def process_use_own_username(call):
    tg = call.message.chat.id
    bot.clear_step_handler_by_chat_id(tg)
    user_data[tg]['username'] = call.from_user.username or ''
    msg = bot.send_message(tg, "Укажите ваш город:")
    bot.register_next_step_handler(msg, process_cache_city)


def process_cache_city(message):
    tg = message.chat.id
    user_data[tg]['city'] = message.text.strip()
    msg = bot.send_message(tg, "Укажите удобное время для связи:")
    bot.register_next_step_handler(msg, process_cache_time)


def process_cache_time(message):
    tg = message.chat.id
    user_data[tg]['desired_time'] = message.text.strip()
    data = user_data[tg]

    qty = Decimal(data['quantity'])
    cny_rate = Decimal(get_rate()[1])
    usdt_r = Decimal(get_cashe())
    raw_cny = (qty / usdt_r) * Decimal(get_usdt()) / cny_rate
    decimal_cny = raw_cny.quantize(Decimal("0.0001"), ROUND_DOWN)
    result_str = str(decimal_cny)
    data['cny'] = result_str

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Вернуться в меню", callback_data="menu"),
        InlineKeyboardButton(
            "Отправить заявку",
            callback_data=(
                f"confirm_cache:"
                f"{data['quantity']}|"
                f"{data['full_name']}|"
                f"{data['username']}|"
                f"{data['city']}|"
                f"{data['desired_time']}|"
                f"{data['cny']}"
            )
        )
    )

    bot.send_message(
        tg,
        (
            f"💱 *Наличная сделка*\n\n"
            f"Сумма: `{data['quantity']}` RUB\n"
            f"ФИО: `{data['full_name']}`\n"
            f"Username: `{data['username']}`\n"
            f"Город: `{data['city']}`\n"
            f"Время связи: `{data['desired_time']}`\n\n"
            f"*Вы получите:* `{result_str}` CNY\n\n"
            "Нажмите «Отправить заявку», чтобы подтвердить, или «Вернуться в меню»."
        ),
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_cache:"))
def confirm_cache_exchange(call):
    tg = call.message.chat.id
    parts = call.data.split("confirm_cache:")[1].split("|")
    if len(parts) != 6:
        return bot.send_message(tg, "⚠️ Ошибка данных, начните заново.")
    qty_text, full_name, username, city, desired_time, cny_text = parts

    try:
        cny_value = Decimal(cny_text)
    except Exception:
        return bot.send_message(tg, "⚠️ Неправильный формат суммы, начните заново.")

    date_str, time_str = get_current_date_time()
    add_service(
        conn,
        'exchange_cache',
        qty_text,
        cny_value,
        city,
        full_name,
        tg,
        username,
        date_str,
        time_str,
        desired_time
    )

    admin_id = get_all_courses(conn)[0][0]
    bot.send_message(
        admin_id,
        (
            "🆕 *Новая наличная сделка*\n\n"
            f"Пользователь: `{tg}` (@{username})\n"
            f"ФИО: `{full_name}`\n"
            f"Сумма: `{qty_text}` RUB\n"
            f"Город: `{city}`\n"
            f"Время связи: `{desired_time}`\n"
            f"Получит: `{cny_text}` CNY"
        ),
        parse_mode="Markdown"
    )

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("В меню", callback_data="menu"))
    bot.send_message(tg, f"✅ Ваша заявка обрабатывается. Администратор: {bot.get_chat(admin_id).username}", reply_markup=kb)
    user_data.pop(tg, None)

if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling()
        except Exception:
            logging.exception("Unexpected error in bot, restarting in 5 seconds")
            time.sleep(5)