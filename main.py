import logging
import Config
import logger

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ContentType
from state import States
from keyboard import geolocation_request_button, build_markup_requests_button
from set_bot_commands import set_default_commands
from exception import ClientException
from client import YandexClient

# Объект бота
bot = Bot(Config.token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
yandexClient = YandexClient()
# Включаем логирование, чтобы не пропустить важные сообщения
log = logger.get_logger()

async def on_startup(dp):
    await set_default_commands(dp)

@dp.message_handler(commands=['start'])
async def send_hi_buttons(message: types.Message):
    await bot.send_message(message.from_user.id, Config.messages['hello'])

@dp.message_handler(commands=['help'])
async def send_reference(message: types.Message):
    await bot.send_message(message.from_user.id, Config.messages['help'])

@dp.message_handler(commands=['cancel'], state="*")
@dp.message_handler(Text(equals="отмена", ignore_case=True), state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(Config.messages['cancel'], reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(commands=['my_place_on_map'])
async def get_my_place_on_map(message: types.Message):
    await bot.send_message(message.chat.id, Config.messages['send_location'], reply_markup=geolocation_request_button)
    await States.NAME_LOCATION.set()

@dp.message_handler(content_types=ContentType.LOCATION, state=States.NAME_LOCATION)
async def get_location_name(message: types.Message, state: FSMContext):
    log.info(message)
    try:
        if message.location is not None:
            address_str = yandexClient.get_geolocation_address_from_coords(message.location)
            if address_str is not None:
                await bot.send_message(message.chat.id, "Ваше местоположение: " + address_str, reply_markup=types.ReplyKeyboardRemove())
            else:
                await message.reply(Config.messages['no_address'])
        else:
            await bot.send_message(message.chat.id, Config.messages['none_location'], reply_markup=types.ReplyKeyboardRemove())
    except ClientException as e:
        await message.reply(Config.args['error'])
    await state.finish()

@dp.message_handler(commands=['search'])
async def start_search_objects(message: types.Message):
    await bot.send_message(message.chat.id, Config.messages['object_name'])
    await States.OBJECT_LOCATION_1.set()

@dp.message_handler(content_types=types.ContentTypes.TEXT, state=States.OBJECT_LOCATION_1)
async def get_near_objects_and_send_location(message: types.Message, state: FSMContext):
    Config.args['name'] = message.text.title()
    await bot.send_message(message.chat.id, Config.messages['send_location'], reply_markup=geolocation_request_button)
    await States.OBJECT_LOCATION_2.set()

@dp.message_handler(content_types=ContentType.LOCATION, state=States.OBJECT_LOCATION_2)
async def get_near_objects_and_send_radius(message: types.Message, state: FSMContext):
    print(message)
    if message.location is not None:
        Config.args['lon'] = message.location.longitude
        Config.args['lat'] = message.location.latitude
        await bot.send_message(message.chat.id, Config.messages['distance'], reply_markup=types.ReplyKeyboardRemove())
        await States.OBJECT_LOCATION_3.set()
    else:
        await bot.send_message(message.chat.id, Config.messages['none_location'], reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(content_types=types.ContentTypes.TEXT, state=States.OBJECT_LOCATION_3)
async def get_near_objects(message: types.Message, state: FSMContext):
    Config.args['radius'] = message.text.title()
    try:
        objects = yandexClient.get_near_objects_by_parameters()
        if (len(objects) != 0):
            async with state.proxy() as data:
                data["objects"] = objects
            await bot.send_message(message.chat.id, Config.messages['places'], reply_markup=build_markup_requests_button(objects))
            await States.OBJECT_LOCATION_4.set()
        else:
            await bot.send_message(message.chat.id, "По запросу " + Config.args['name'] + " с радиусом поиска " + Config.args['radius'] + " м. ничего не найдено", reply_markup=types.ReplyKeyboardRemove())    
            await state.finish()
    except ClientException as e:
        await message.reply(Config.args['error'])
        await state.finish()

@dp.callback_query_handler(text_contains='near_object_next_state_', state=States.OBJECT_LOCATION_4)
async def process_callback_mono(call: types.CallbackQuery, state: FSMContext):
    log.info("Click button: {0}".format(str(call)))
    try:
        if call.data and call.data.startswith("near_object_next_state_"):
            data = await state.get_data()
            dictionary: States = data.get("objects")
            code = call.data[-1:]
            if code.isdigit():
                code = int(code)
            else:
                await bot.answer_callback_query(call.id)
                return
            buttons = call.message.reply_markup.inline_keyboard
            for button in buttons:
                codeNumberButton = button[0].callback_data[-1:]
                if codeNumberButton.isdigit():
                    codeNumberButton = int(codeNumberButton)
                if code == codeNumberButton:
                    objectData = dictionary[code]
                    await bot.send_message(call.message.chat.id, objectData.buildAllInfo())
                    coordPoint = yandexClient.get_coords_from_address(objectData.getAddress())
                    log.info("coordination {0}".format(coordPoint))
                    coords = str(coordPoint).split()
                    await bot.send_location(call.message.chat.id, latitude=coords[1], longitude=coords[0], live_period=1200, proximity_alert_radius=20)
                    break
        else:
            await bot.send_message(call.message.chat.id, Config.args['error'])
    except ClientException as e:
        await bot.send_message(call.message.chat.id, Config.args['error'])
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
