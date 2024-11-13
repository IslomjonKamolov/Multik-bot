import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from states import AdminStates
from dataBase import add_code, get_url_by_code, check_code_exists, create_table
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_ID
from aiogram.fsm.context import FSMContext

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

create_table()
print('I AM RUNNING')


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        f"Salom {message.from_user.full_name}!\n\nMen sizga multfilm yuboraman. Buning uchun menga multfilm kodini yuboring!"
    )


# Admin panelini ochish
@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if message.from_user.id in ADMIN_ID:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Yangi kod", callback_data="new_code")]
            ]
        )
        await message.answer(
            "Xo'sh janob, bugun nimani o'zgartiramiz?", reply_markup=keyboard
        )
    else:
        await message.answer("Siz admin emasiz!")


# Yangi kod tugmasi bosilganda
@dp.callback_query(lambda c: c.data == "new_code")
async def new_code_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in ADMIN_ID:
        await callback.message.answer("Kod kiriting:")
        await state.set_state(AdminStates.enter_code)


# Admin kod kiritganda
@dp.message(AdminStates.enter_code)
async def enter_code(message: types.Message, state: FSMContext):
    code = message.text
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Boshqa kod kiritish", callback_data="new_code")]
        ]
    )
    # Tekshirish: kod avvaldan mavjudmi
    if check_code_exists(code):
        await message.answer(
            "Uzur janob bu kodni allaqachon band qilib qo'yishgan :(",
            reply_markup=keyboard,
        )
        await state.clear()
        return

    await state.update_data(code=code)
    await message.answer("URL manzilini kiriting:")
    await state.set_state(AdminStates.enter_url)


# Admin URL kiritganda
@dp.message(AdminStates.enter_url)
async def enter_url(message: types.Message, state: FSMContext):
    data = await state.get_data()
    code = data.get("code")
    url = message.text
    await state.update_data(url=url)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha", callback_data="confirm_yes"),
                InlineKeyboardButton(text="Yo'q", callback_data="confirm_no"),
            ]
        ]
    )
    await message.answer(
        f"<b>Yangi qo'shiladigan ma'lumotlar:</b>\nKod: {code}\nURL: {url}\n<b>Bu mal'lumotlarni qo'shamizmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.confirm)


# Tasdiqlash bosqichi
@dp.callback_query(AdminStates.confirm, lambda c: c.data == "confirm_yes")
async def confirm_save(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    code = data["code"]
    url = data["url"]

    # Kod va URL'ni saqlash
    add_code(code, url)
    await callback.message.answer("Kod va URL saqlandi!")
    # Boshqa adminlarga xabar yuborish
    for admin_id in ADMIN_ID:
        if admin_id != callback.from_user.id:
            await bot.send_message(
                admin_id, f"Admin {callback.from_user.id} kod '{code}' ni qo'shdi."
            )

    await state.clear()


@dp.callback_query(AdminStates.confirm, lambda c: c.data == "confirm_no")
async def confirm_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Bekor qilindi.")
    await state.clear()


# Foydalanuvchi tomonidan kod yuborilganda
@dp.message()
async def check_code(message: types.Message):
    code = message.text
    url = get_url_by_code(code)
    if url:
        await message.answer(f"👇👇👇 Multfilm mana bu yerda 👇👇👇\n{url}")
    else:
        await message.answer("Bunday kod topilmadi. Iltimos yaxshilab tekshirib ko'ring.")


if __name__ == "__main__":
    dp.run_polling(bot)
