import requests
from xml.etree import ElementTree as ET
import json
import csv
from collections import namedtuple
from abc import ABC, abstractmethod

FloatNumber = namedtuple('FloatNumber', ['integer', 'fractional'])

class CurrenciesListInterface(ABC):
    @abstractmethod
    def get_currencies(self):
        pass

class CurrenciesList(CurrenciesListInterface):
    def __init__(self, currency_codes=None):
        self.currency_codes = currency_codes

    def get_currencies(self):
        try:
            response = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Ошибка при запросе данных: {e}")
            return []

        root = ET.fromstring(response.content)
        valutes = root.findall("Valute")
        result = []

        for valute in valutes:
            valute_id = valute.get('ID')
            if self.currency_codes is None or valute_id in self.currency_codes:
                name = valute.find('Name').text
                value = valute.find('Value').text.replace(',', '.')
                nominal = int(valute.find('Nominal').text)
                char_code = valute.find('CharCode').text

                integer, fractional = value.split('.')
                float_number = FloatNumber(integer, fractional)

                if nominal != 1:
                    adjusted_value = FloatNumber(
                        str(round(float(value) / nominal, 2)).split('.')[0],
                        str(round(float(value) / nominal, 2)).split('.')[1]
                    )
                    result.append({char_code: (name, adjusted_value)})
                else:
                    result.append({char_code: (name, float_number)})

        return result

class CurrenciesDecorator(CurrenciesListInterface):
    def __init__(self, component: CurrenciesListInterface):
        self._component = component

    def get_currencies(self):
        return self._component.get_currencies()

class ConcreteDecoratorJSON(CurrenciesDecorator):
    def get_currencies(self):
        data = self._component.get_currencies()
        return json.dumps(data, ensure_ascii=False, indent=4)

class ConcreteDecoratorCSV(CurrenciesDecorator):
    def get_currencies(self):
        data = self._component.get_currencies()
        csv_data = [['Код валюты', 'Название', 'Курс (RUB)']]

        for currency in data:
            for code, (name, value) in currency.items():
                csv_data.append([code, name, f"{value.integer}.{value.fractional}"])

        return csv_data

if __name__ == "__main__":
    base_currencies = CurrenciesList(currency_codes=['R01035', 'R01335', 'R01700J'])
    print("Базовый формат:")
    print(base_currencies.get_currencies())

    json_decorator = ConcreteDecoratorJSON(base_currencies)
    print("\nФормат JSON:")
    print(json_decorator.get_currencies())

    csv_decorator = ConcreteDecoratorCSV(base_currencies)
    print("\nФормат CSV:")
    csv_data = csv_decorator.get_currencies()
    for row in csv_data:
        print(row)
