import config
import logging
import telebot
from telebot import types
from functions import (
    DrugPaginationModel,
    search_drug,
    drug_detailed,
    drug_detailed_data_clean,
    get_param,
    get_image,
    create_menu
)

bot = telebot.TeleBot(config.TOKEN)

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, f'Я Доктор Гретта. Приятно познакомиться с вами, {message.from_user.first_name}')
    bot.reply_to(message, f'Отправьте мне название лекарства и я предоставлю вам его аналоги.')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower():
        results = search_drug(message.text.lower())
        if len(results) == 0:
            bot.send_message(message.from_user.id, 'К сожалению в базе отсутсвует данное лекарство.')
        else:
            pagination = DrugPaginationModel(results, 4)
            reply_markup = create_menu(pagination.page_items, 'name', 'id')
            load_more = types.InlineKeyboardButton("Загрузи больше", callback_data = "%s,%s,%s" % (message.text.lower(), "load_more", str(pagination.current_page_number)))
            reply_markup.add(load_more)
            bot.send_message(message.from_user.id, 'Результаты поиска: %s' % message.text, reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data.isdigit(): #Проверка если это кнопка лекарства
            result = drug_detailed(call.data)
            image_url = get_image(result['imageName'])
            bot.send_photo(call.message.chat.id, image_url)

            button_list = []
            markup = types.InlineKeyboardMarkup(row_width=2)
            clean_data = drug_detailed_data_clean(result)
            for key in clean_data:
                button_list.append(types.InlineKeyboardButton(
                    key,
                    callback_data = key + ',' + call.data,
                ))
            markup.add(*button_list)

            bot.send_message(call.message.chat.id, '*Название: %s*' % result['name'], parse_mode="Markdown")
            bot.send_message(call.message.chat.id, '*Цена: %s*' % result['price'], parse_mode="Markdown")
            bot.send_message(call.message.chat.id, '*Отпуск: %s*' % result['dispensedByPrescription'], parse_mode="Markdown")
            bot.send_message(call.message.chat.id, 'Подробная информация', reply_markup=markup)
        elif 'load_more' in call.data.split(','):
            data = call.data.split(',')
            results = search_drug(data[0])
            pagination = DrugPaginationModel(results, 4)
            pagination._current_page = int(data[2])
            if pagination.has_next_page:
                pagination.flip_next_page()

                reply_markup = create_menu(pagination.page_items, 'name', 'id')
                load_more = types.InlineKeyboardButton("Загрузи больше", callback_data = "%s,%s" % (data[0], "load_more"))
                reply_markup.add(load_more)
                bot.send_message(call.message.chat.id, 'Результаты поиска: %s' % data[0], reply_markup=reply_markup)
            else:
                bot.send_message(call.message.chat.id, 'Больше нет данных')
        else:#Проверка если это кнопка параметра
            results, drug_id = get_param(call.data)
            button_list = []
            markup = types.InlineKeyboardMarkup(row_width=2)
            if isinstance(results, list):#проверка если кликнули аналоги
                reply_markup = create_menu(results, 'name', 'id')
                bot.send_message(call.message.chat.id, 'Подробная информация', reply_markup=reply_markup)
            else:
                bot.send_message(call.message.chat.id, results)
            #Также нужно уловить случай с аналогом

    except Exception as e:
        print(repr(e))


bot.polling(none_stop=True)
