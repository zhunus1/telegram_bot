import requests
import json
import urllib.parse
import re
from telebot import types


class DrugPaginationModel:
    def __init__(self, all_items, items_per_page = 4):
        self.all_items = list(all_items or [])
        self._current_page = 0
        self.items_per_page = items_per_page

    @property
    def _begin(self):
        return self._current_page * self.items_per_page

    @property
    def _end(self):
        return min((self._current_page + 1) * self.items_per_page, self.item_count)

    @property
    def item_count(self):
        return len(self.all_items)

    @property
    def page_items(self):
        return self.all_items[self._begin : self._end]

    @property
    def current_page_number(self):
        return self._current_page + 1

    @property
    def has_next_page(self):
        return self._end < self.item_count

    @property
    def has_previous_page(self):
        return self._begin > 0

    def flip_next_page(self):
        self._current_page += 1

    def flip_previous_page(self):
        self._current_page -= 1


def search_drug(drugName):
    search_url = 'http://doctor-gretta.kz/api/drugs/search/%s' % urllib.parse.quote(drugName)
    response = requests.get(search_url)
    return response.json()
  # [{
  #   "id": 734,
  #   "name": "Но-шпа 40 мг 2,0 №5",
  #   "searchName": null,
  #   "activeSubstanceId": null,
  #   "activeSubstance": null,
  #   "imageName": "2019_20_01_06_09_00_684.jpg",
  #   "price": "1 540 тг",
  #   "dosageForm": null,
  #   "producingCountry": null,
  #   "structure": null,
  #   "dispensedByPrescription": null,
  #   "indications": null,
  #   "methodOfAdministrationAndDosage": null,
  #   "contraindications": null,
  #   "sideEffects": null,
  #   "description": null,
  #   "similarDrugs": null
  # }],


def drug_detailed(drug_id):
    search_url = 'http://doctor-gretta.kz/api/drugs/id/%s' % drug_id
    response = requests.get(
        search_url,
    )
    return response.json()
# {
#   "id": 0,
#   "name": "string",
#   "searchName": "string",
#   "activeSubstanceId": 0,
#   "activeSubstance": "string",
#   "imageName": "string",
#   "price": "string",
#   "dosageForm": "string",
#   "producingCountry": "string",
#   "structure": "string",
#   "dispensedByPrescription": "string",
#   "indications": "string",
#   "methodOfAdministrationAndDosage": "string",
#   "contraindications": "string",
#   "sideEffects": "string",
#   "description": "string",
#   "similarDrugs": [
#     "string"
#   ]
# }


def drug_detailed_data_clean(data):
    for key in data:
        if data[key] == None or data[key] == '':
            data[key] = "Данные отсутсвуют"

    clean_data = {
        'Название': data['name'],
        'Субстанция': data['activeSubstance'],
        'Форма дозы': data['dosageForm'],
        'Страна изготовитель': data['producingCountry'],
        'Состав': data['structure'],
        'Показания к применению': data['indications'],
        'Инструкция к применению': data['methodOfAdministrationAndDosage'],
        'Противопоказания': data['contraindications'],
        'Побочные эффекты': data['sideEffects'],
        'Описание': data['description'],
        'Аналоги': data['similarDrugs'],
    }
    return clean_data


def get_param(list):
    params = list.split(',')
    data = drug_detailed(params[1])
    clean_data = drug_detailed_data_clean(data)
    return clean_data[params[0]], params[1], clean_data['Название']


def get_image(image_name):
    no_image_url = 'http://doctor-gretta.kz/AllDrugImages/NoPhoto.jpg'
    search_url = 'http://doctor-gretta.kz/AllDrugImages/%s' % image_name
    response = requests.get(
        search_url,
    )
    if response.status_code == 200:
        return search_url
    else:
        return no_image_url


def create_menu(results, param_1, param_2):
    button_list = []
    markup = types.InlineKeyboardMarkup(row_width=2)
    for result in results:
        button_list.append(types.InlineKeyboardButton(
            result[param_1],
            callback_data = result[param_2]
        ))

    markup.add(*button_list)
    return markup
