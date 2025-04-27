# config.py
from pinoywok.config import config
from pinoywok.logging import log
import json
import requests
import unicodedata

class Api:
    _instance = None

    def __new__(self):
        if self._instance is None:
            self._instance = super(Api, self).__new__(self)
            self._instance = Api()
            #self._instance.load_config(file)
        return self._instance

    def get_order(self,id):
        # The URL of the API endpoint
        url = f'{config.get_orders_api()}/{id}'

        # Making a GET request
        # Set the Bearer token in the Authorization header
        headers = {
            'Authorization': f'Bearer {config.get_orders_api_key()}'
        }

        # Making a GET request with the Bearer token
        #response = requests.get(url, headers=headers)
        response = requests.get(url,headers=headers)
        log(url)
        log(response)
        text = unicodedata.normalize('NFKD', response.text).encode('ascii', 'ignore').decode('utf-8').replace("\n", "")
        #log(json.loads(text))
        return json.loads(text)
    
    def parse_order_content(self,orderJson):
        
        #if "provider" in orderJson and "action" in orderJson and "body" in orderJson:
        #        _id = orderJson["id"]
        #        provider = orderJson["provider"]
        #        action = orderJson["action"]
        #        payload = orderJson["body"]["payload"]
        #else:
        #    return {}
        return json.loads(orderJson["body"]["payload"])

    

api = Api()
