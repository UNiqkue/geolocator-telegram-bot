from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton

geolocation_request_button = ReplyKeyboardMarkup(resize_keyboard=True)
geolocation_request_button.add(KeyboardButton('Отправить свое местоположение', request_location=True))

def build_markup_requests_button(dictionary):
    markup_requests_button = InlineKeyboardMarkup()
    for key in dictionary.keys():
        objectData = dictionary[key]
        message = str(key) + ". " + objectData.buildMinInfo()
        callback_data_number = 'near_object_next_state_' + str(key)
        markup_requests_button.add(InlineKeyboardButton(message, callback_data=callback_data_number))
    return markup_requests_button
