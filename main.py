import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from config import TG_TOKEN, CHANEL_ID

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class Form(StatesGroup):
    name = State()
    citizenship = State()
    age = State()
    work_type = State()
    phone = State()
    confirm = State()


@dp.message(F.text == '/start')
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Введите Ваше имя.")
    await state.set_state(Form.name)


@dp.message(F.data == 'confirm_no')
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Введите Ваше имя.")
    await state.set_state(Form.name)


@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="РФ", callback_data="citizenship_ru"))
    builder.add(types.InlineKeyboardButton(text="РБ", callback_data="citizenship_by"))
    builder.add(types.InlineKeyboardButton(text="Иное", callback_data="citizenship_other"))

    await message.answer("Гражданство:", reply_markup=builder.as_markup())
    await state.set_state(Form.citizenship)


@dp.callback_query(F.data.startswith("citizenship"), Form.citizenship)
async def process_citizenship(callback: types.CallbackQuery, state: FSMContext):
    citizenship = callback.data.split('_')[1]

    if citizenship == 'other':
        await callback.message.answer("Извините, на данный момент мы не готовы предложить вам работу")
        await state.clear()
    else:
        await state.update_data(citizenship=citizenship)
        await callback.message.answer("Введите ваш возраст.")
        await state.set_state(Form.age)

    await callback.answer()


@dp.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Возраст должен быть числом! Введите еще раз:")
        return

    await state.update_data(age=int(message.text))

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Работа с проживанием (вахта)",
        callback_data="work_type_1"))
    builder.add(types.InlineKeyboardButton(
        text="Подработка",
        callback_data="work_type_2"))
    builder.adjust(1)
    await message.answer("Тип работы:", reply_markup=builder.as_markup())
    await state.set_state(Form.work_type)


@dp.callback_query(F.data.startswith("work_type"), Form.work_type)
async def process_work_type(callback: types.CallbackQuery, state: FSMContext):
    work_type = {
        'work_type_1': 'Работа с проживанием (вахта)',
        'work_type_2': 'Подработка'
    }[callback.data]

    await state.update_data(work_type=work_type)

    await callback.message.answer(
        "Введите ваш телефон."
    )
    await state.set_state(Form.phone)
    await callback.answer()


@dp.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)

    data = await state.get_data()

    text = f"Проверьте данные:\n\nИмя: {data['name']}\nГражданство: {data['citizenship'].upper()}\nВозраст: {data['age']}\nТип работы: {data['work_type']}\nТелефон: {phone}"

    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Подтвердить",
        callback_data="confirm_yes"))
    builder.add(types.InlineKeyboardButton(
        text="Начать заново",
        callback_data="confirm_no"))

    await message.answer(text, reply_markup=builder.as_markup())
    await state.set_state(Form.confirm)


@dp.callback_query(F.data.startswith("confirm"), Form.confirm)
async def process_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'confirm_yes':
        data = await state.get_data()

        # Отправка в группу
        await bot.send_message(
            chat_id=CHANEL_ID,
            text=f"Новая анкета:\n\n"
                 f"Имя: {data['name']}\n"
                 f"Гражданство: {data['citizenship'].upper()}\n"
                 f"Возраст: {data['age']}\n"
                 f"Тип работы: {data['work_type']}\n"
                 f"Телефон: {data['phone']}"
        )

        await callback.message.answer(
            "Спасибо, Ваша анкета передана менеджерам. "
            "В ближайшее время они ее обработают и свяжутся с Вами."
        )
    else:
        await start_handler(callback.message, state)

    await state.clear()
    await callback.answer()


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(filename)s:%(lineno)d %(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')
    logging.info('Starting bot')

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
