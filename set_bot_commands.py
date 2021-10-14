from aiogram import types

async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("my_place_on_map", "Определить местоположение"),
        types.BotCommand("search", "Найти ближайшие магазины/кафе/заведения/парки и т.д."),
        types.BotCommand("help", "Посмотреть справку"),
        types.BotCommand("cancel", "Отменить действие"),
    ])