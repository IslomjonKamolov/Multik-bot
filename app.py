import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from states import AdminStates
from dataBase import add_code, get_url_by_code, check_code_exists, create_table
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_ID, CHANNELS
from aiogram.fsm.context import FSMContext
from functions import check_channel
from aiogram.utils.keyboard import InlineKeyboardBuilder


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class ChannelCallback(CallbackData, prefix="channel"):
    url: str



def create_channel_buttons():
    keyboard_builder = InlineKeyboardBuilder()
    for index, channel_url in enumerate(CHANNELS):
        channel_name = channel_url.replace("https://t.me/", "")
        # `callback_data` sifatida faqat unikal identifikator yoki indeksdan foydalanamiz
        keyboard_builder.button(text=f"❌ {channel_name}", callback_data=f"remove_{index}")
    return keyboard_builder.adjust(1).as_markup()



create_table()


async def is_subscribe(message):
    response = await check_channel(userId=message.from_user.id, bot=bot)
    if response:
        return True
    else:
        return False


@dp.message(CommandStart())
async def start(message: types.Message):
    is_subscribed = await is_subscribe(message=message)

    if not is_subscribed:
        keyboard_builder = InlineKeyboardBuilder()
        for channel_url in CHANNELS:
            channel_name = channel_url.replace("https://t.me/", "")
            keyboard_builder.button(text=channel_name, url=channel_url)

        await message.answer(
            "Siz kanallarga obuna bo'lmagan ko'rinasiz. Iltimos barcha kanallarga obuna bo'ling!!!",
            reply_markup=keyboard_builder.adjust(1).as_markup(),
        )
        return

    await message.answer(
        f"Salom {message.from_user.full_name}!\n\nMen sizga multfilm yuboraman. Buning uchun menga multfilm kodini yuboring!"
    )


# Admin panelini ochish
@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if message.from_user.id in ADMIN_ID:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Yangi kod qo'shish", callback_data="new_code"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Yangi kanal qo'shish", callback_data="new_channel"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Kanalni olib tashlash", callback_data="delete_channel"
                    )
                ],
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


@dp.callback_query(lambda c: c.data == "new_channel")
async def new_channel_fun(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in ADMIN_ID:
        await callback.message.answer(
            "Kanal url manzilini kiriting!\n<b>Namuna:</b>\nhttps://t.me/username",
            parse_mode="HTML",
        )
        await state.set_state(AdminStates.new_channel)


@dp.callback_query(lambda c: c.data == "delete_channel")
async def delete_channel_handler(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id in ADMIN_ID:
        await callback.message.answer("Kanalni tanlang:", reply_markup=create_channel_buttons())

@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def remove_channel_fun(callback: types.CallbackQuery):
    if callback.from_user.id in ADMIN_ID:
        # `callback.data` dan kanal indeksini olish
        channel_index = int(callback.data.split("_")[1])

        if 0 <= channel_index < len(CHANNELS):
            removed_channel = CHANNELS.pop(channel_index)
            await callback.message.answer(f"🔴 {removed_channel} kanali o'chirildi!")
        else:
            await callback.message.answer("Kanal topilmadi!")

        # Yangi ro'yxatni ko'rsatish
        if CHANNELS:
            await callback.message.answer(
                "Qolgan kanallar:",
                reply_markup=create_channel_buttons()
            )
        else:
            await callback.message.answer("Hozircha kanallar ro'yxati bo'sh.")

@dp.callback_query(ChannelCallback.filter())
async def delete_channel_callback(
    callback: types.CallbackQuery, callback_data: ChannelCallback
):
    global CHANNELS
    channel_url = callback_data.url

    # Kanal ro'yxatdan o'chiriladi
    if channel_url in CHANNELS:
        CHANNELS.remove(channel_url)
        await callback.answer(f"✅ {channel_url} o'chirildi")
    else:
        await callback.answer("Bu kanal ro'yxatda topilmadi", show_alert=True)

    # Yangi holat bo'yicha tugmalarni yangilash
    if CHANNELS:
        await callback.message.edit_text(
            "Quyidagi kanallar ro'yxatini tanlab o'chirishingiz mumkin:",
            reply_markup=create_channel_buttons(),
        )
    else:
        await callback.message.edit_text("Hozircha kanallar ro'yxati bo'sh.")


@dp.message(AdminStates.new_channel)
async def new_channel(message: types.Message, state: FSMContext):
    url = message.text
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="ha")], [KeyboardButton(text="yo'q")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await state.update_data(new_channel=url)
    await message.answer(
        f"Haqiqatdan ham {url} urlni qo'shmoqchimisiz?", reply_markup=keyboard
    )
    await state.set_state(AdminStates.confirm_channel)


@dp.message(AdminStates.confirm_channel)
async def new_channel_confirmation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    channel_url = data.get("new_channel")
    CHANNELS.append(channel_url)
    await message.answer(
        f"siz kiritgan kanal: {channel_url}.", reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


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
    is_subscribed = await is_subscribe(message=message)

    if not is_subscribed:
        keyboard_builder = InlineKeyboardBuilder()
        for channel_url in CHANNELS:
            channel_name = channel_url.replace("https://t.me/", "")
            keyboard_builder.button(text=channel_name, url=channel_url)

        await message.answer(
            "Siz kanallarga obuna bo'lmagan ko'rinasiz. Iltimos barcha kanallarga obuna bo'ling!!!",
            reply_markup=keyboard_builder.adjust(1).as_markup(),
        )
        return
    code = message.text
    url = get_url_by_code(code)
    if url:
        await message.answer(f"👇👇👇 Multfilm mana bu yerda 👇👇👇\n{url}")
    else:
        await message.answer(
            "Bunday kod topilmadi. Iltimos yaxshilab tekshirib ko'ring."
        )


if __name__ == "__main__":
    dp.run_polling(bot)
