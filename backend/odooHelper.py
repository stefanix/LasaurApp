import requests
from requests.auth import HTTPBasicAuth
#import BeautifulSoup
import re
import json


class OdooHelper:

    def __init__(self, username, password, url, db):
        self.username = username
        self.password = password
        self.url = url
        self.db = db

        #Open Session with Odoo
        self.session = requests.session()
        req1 = self.session.get(self.url + "/web")
        self.csrf_token = re.findall(r'name="csrf_token" value="(.+?)"', req1.content)
        payload = {
            "login": "admin@admin.de",
            "password": "admin",
            "csrf_token": self.csrf_token,
        }
        self.session.post(self.url + "/web/login", data=payload)

        #test if authentification is successful
        #req2 = self.session.get(self.url + "/web")
        #TODO find way of checking if /web/login or /web get reached
        #print(req2.content)

    def callAPI(self, path, args=None):
        req = self.session.post(self.url + path, data={"csrf_token": self.csrf_token})
        return json.loads(req.content)
