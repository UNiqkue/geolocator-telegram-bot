from model import ObjectData
from os import name
import Config
import requests
import logger
import math

from exception import ClientException

log = logger.get_logger()

class YandexClient:

    def __init__(self):
        self.latitude_angle_spn = 360.0 * math.sin(math.pi/180*45.0)
        self.longitude_angle_spn = 360.0 * math.cos(math.pi/180*45.0)

    def get_geolocation_address_from_coords(self, location):
        Config.args['lon'] = location.longitude
        Config.args['lat'] = location.latitude
        coords = repr(Config.args['lon']) + "," + repr(Config.args['lat'])

        PARAMS = {
            "apikey":Config.geocodeapikey,
            "format":"json",
            "lang":"ru_RU",
            "kind":"house",
            "geocode":coords
        }

        #отправляем запрос по адресу геокодера.
        try:
            response = requests.get(url=Config.yandex_geocode_url, params=PARAMS)
            #получаем данные
            json_data = response.json()
            log.info("Response data {0}".format(json_data))
            #вытаскиваем из всего пришедшего json именно строку с полным адресом.
            featureMembers = json_data["response"]["GeoObjectCollection"]["featureMember"]
            #проверяем пустой ли список, потому что существуют места без адресов
            if not featureMembers:
                address_str = None
            else:
                address_str = featureMembers[0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["AddressDetails"]["Country"]["AddressLine"]
            #возвращаем полученный адрес
            return address_str
        except Exception as e:
            #если не смогли, то возвращаем ошибку
            log.error(e)
            raise ClientException

    def get_coords_from_address(self, address):

        PARAMS = {
            "apikey":Config.geocodeapikey,
            "format":"json",
            "lang":"ru_RU",
            "kind":"house",
            "geocode":address
        }

        try:
            response = requests.get(url=Config.yandex_geocode_url, params=PARAMS)
            json_data = response.json()

            log.info("Response data {0}".format(json_data))
            
            featureMembers = json_data["response"]["GeoObjectCollection"]["featureMember"]
            if not featureMembers:
                coordination = None
            else:
                coordination = featureMembers[0]["GeoObject"]["Point"]["pos"]
            return coordination
        except Exception as e:
            log.error(e)
            raise ClientException


    def get_near_objects_by_parameters(self):
        latitude_spn = self.latitude_angle_spn * float(Config.args['radius']) / (40008550.0)
        longitude_spn = self.longitude_angle_spn * float(Config.args['radius']) / (40075696.0 * math.cos(math.pi/180*float(Config.args['lat'])))

        lat_top_right = Config.args['lat'] + latitude_spn
        lon_top_right = Config.args['lon'] + longitude_spn
        lat_bottom_left = Config.args['lat'] - latitude_spn
        lon_bottom_left = Config.args['lon'] - longitude_spn

        coords = repr(lon_bottom_left) + "," + repr(lat_bottom_left) + "~" + repr(lon_top_right) + "," + repr(lat_top_right)

        PARAMS = {
            "apikey":Config.geosearchapikey,
            "text":Config.args['name'],
            "bbox":coords,
            "type":"biz",
            "results":9,
            "lang":"ru_RU"
        }

        try:
            response = requests.get(url=Config.yandex_geosearch_url, params=PARAMS)
            json_data = response.json()
            log.info(json_data)
            return self.build_dictionary_objects_data(json_data)
        except Exception as e:
            log.error(e)
            raise ClientException
            
    @staticmethod
    def build_dictionary_objects_data(json_data):
        dictionary = {}
        number = 1
        for org in json_data['features']:
            name = org['properties']['name']
            address = org['properties']['description']

            categoriesList = []
            companyMetaData = org['properties']['CompanyMetaData']
            for category in companyMetaData['Categories']:
                categoriesList.append(category['name'])

            time = None
            if companyMetaData.get('Hours') is not None:
                time = companyMetaData['Hours']['text']
            
            url = None
            if companyMetaData.get('url') is not None:
                url = companyMetaData['url']

            object_data = ObjectData(name, address, categoriesList, time, url)
            dictionary[number] = object_data
            log.info(object_data)
            number+=1
        log.info(dictionary)
        return dictionary