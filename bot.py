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

#Приветствие бота
@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.reply_to(message, f'Я Доктор Гретта. Приятно познакомиться с вами, {message.from_user.first_name}')
    bot.reply_to(message, f'Отправьте мне название лекарства и я предоставлю вам его аналоги.')


#Принимаем ответ от юзера
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower():
        drug_name = message.text.lower()
        results = search_drug(drug_name)
        if len(results) == 0: #Если нет лекарства
            bot.send_message(message.from_user.id, 'К сожалению в базе отсутствуют данные касательно данного препарата.')
            bot.send_message(message.from_user.id, 'Попробуйте повторить поиск по другому названию')
        else:
            reply_markup = create_menu(results, 'name', 'id')
            image_url = get_image(results[0]['imageName'])

            bot.send_photo(message.from_user.id, image_url)
            bot.send_message(message.from_user.id, '*Название: %s*' % results[0]['name'], parse_mode = "Markdown")
            bot.send_message(message.from_user.id, '*Цена: %s*' % results[0]['price'], parse_mode = "Markdown")
            bot.send_message(message.from_user.id, 'Результаты поиска: %s' % message.text, reply_markup = reply_markup)

#Обрабатываем нажатия на кнопки
pagination = None
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global pagination
    try:
        #Проверка если это кнопка препарата в меню
        if call.data.isdigit():
            drug_id = call.data
            result = drug_detailed(drug_id)
            image_url = get_image(result['imageName'])
            bot.send_photo(call.message.chat.id, image_url)

            button_list = []
            markup = types.InlineKeyboardMarkup(row_width=2)
            clean_data = drug_detailed_data_clean(result)

            for parameter in clean_data:
                button_list.append(types.InlineKeyboardButton(
                    parameter,
                    callback_data = parameter + ',' + drug_id,
                ))
            markup.add(*button_list)

            bot.send_message(call.message.chat.id, '*Название: %s*' % result['name'], parse_mode = "Markdown")
            bot.send_message(call.message.chat.id, '*Цена: %s*' % result['price'], parse_mode = "Markdown")
            bot.send_message(call.message.chat.id, '*Отпуск: %s*' % result['dispensedByPrescription'], parse_mode = "Markdown")
            bot.send_message(call.message.chat.id, 'Подробная информация', reply_markup = markup)

        #Проверка если это кнопка Загрузить больше лекарств
        elif 'load_more' in call.data:

            if pagination.has_next_page:
                pagination.flip_next_page()

                reply_markup = create_menu(pagination.page_items, 'name', 'id')
                load_more = types.InlineKeyboardButton("Загрузи больше", callback_data = "load_more")
                reply_markup.add(load_more)
                bot.send_message(call.message.chat.id, 'Страница №%s' % str(pagination.current_page_number), reply_markup=reply_markup)
            else:
                bot.send_message(call.message.chat.id, 'Больше нет данных')

        #Проверка если это кнопка параметра препарата
        else:
            results, drug_id, drug_name = get_param(call.data)
            button_list = []
            markup = types.InlineKeyboardMarkup(row_width=2)
            #Проверка если кликнули на кнопку Аналоги
            if isinstance(results, list):
                pagination = DrugPaginationModel(results, 4)
                reply_markup = create_menu(pagination.page_items, 'name', 'id')

                load_more = types.InlineKeyboardButton("Загрузи больше", callback_data = "load_more")
                reply_markup.add(load_more)

                bot.send_message(call.message.chat.id, 'Страница №%s' % str(pagination.current_page_number), reply_markup=reply_markup)
            else:
                bot.send_message(call.message.chat.id, results)


    except Exception as e:
        print(repr(e))


bot.polling(none_stop=True)
