import subprocess
import sys
import importlib

# ==================== АВТОУСТАНОВКА БИБЛИОТЕК ====================
REQUIRED = {
    "aiogram": "aiogram",
    "python-dotenv": "dotenv",
}

def install_packages():
    for pip_name, import_name in REQUIRED.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"[УСТАНОВКА] {pip_name} ...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pip_name, "--quiet"]
            )

install_packages()

# ==================== ИМПОРТЫ ====================
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

# ==================== ЗАГРУЗКА ТОКЕНА ====================
# Токен берётся из .env рядом со скриптом, или из переменной окружения
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    print(
        "\n[ОШИБКА] BOT_TOKEN не найден.\n"
        "Создай файл .env рядом с bot.py со строкой:\n"
        "BOT_TOKEN=твой_токен_от_BotFather\n"
    )
    sys.exit(1)

# ==================== ДАННЫЕ ====================
PRODUCT_NAME = "immortal.rip"
CURRENCIES = "₽ RUB  и  ₸ KZT"

# Реселлеры: отображаемое имя -> username без @
RESELLERS = {
    "Frey101": "Frey101",
    "Floksys": "Floksys",
}

# ==================== ЛОГИРОВАНИЕ ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ==================== БОТ ====================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 Наши реселлеры",
                    callback_data="resellers",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💵 Оплата и цены",
                    callback_data="payment",
                )
            ],
        ]
    )


def resellers_menu() -> InlineKeyboardMarkup:
    rows = []
    for display, username in RESELLERS.items():
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"💬 {display}",
                    url=f"https://t.me/{username}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")]
        ]
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        f"👋 <b>Добро пожаловать!</b>\n\n"
        f"🏪 Наш товар: <b>{PRODUCT_NAME}</b>\n\n"
        f"💵 Принимаем: <b>{CURRENCIES}</b>\n\n"
        f"👇 Выбери действие:"
    )
    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode=ParseMode.HTML,
    )


@dp.callback_query(F.data == "resellers")
async def show_resellers(callback: CallbackQuery):
    lines = ["🤝 <b>Наши реселлеры:</b>\n"]
    for display, username in RESELLERS.items():
        lines.append(f"• @{username}")
    lines.append("\n📩 Напиши любому из них для покупки 👇")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=resellers_menu(),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@dp.callback_query(F.data == "payment")
async def show_payment(callback: CallbackQuery):
    text = (
        "💵 <b>Оплата</b>\n\n"
        "Принимаем:\n"
        "• 🇷🇺 <b>Рубли (₽ RUB)</b>\n"
        "• 🇰🇿 <b>Тенге (₸ KZT)</b>\n\n"
        f"🛒 Товар: <b>{PRODUCT_NAME}</b>\n\n"
        "📩 Для оформления заказа напиши нашему реселлеру."
    )
    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    text = (
        f"👋 <b>Добро пожаловать!</b>\n\n"
        f"🏪 Наш товар: <b>{PRODUCT_NAME}</b>\n\n"
        f"💵 Принимаем: <b>{CURRENCIES}</b>\n\n"
        f"👇 Выбери действие:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=main_menu(),
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


# ==================== ЗАПУСК ====================
async def main():
    print("[БОТ] Запуск...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n[БОТ] Остановлен.")