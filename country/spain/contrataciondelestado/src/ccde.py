import sys
import requests
import re
import os
import json
import asyncio
import bugsnag

sys.path.append("../../../../utils")
sys.path.append("../../../../")

from driver import *
from tokenizer import *
from location_db import *

from datetime import datetime

# Contratantes de Contratacion Del Estado
class CCDE:

    def __init__ (self, soup):

        if not soup:
            soup = get_soup_from_url(url, "html.parser")

        #...
        self.nombre                 = self.find_text_by_id(soup, 'span', 'perfilComp:idOrg')
        self.url_fuente             = self.get_url(soup)
        self.enlace                 = self.url_fuente
        self.pais                   = self.find_text_by_id(soup, 'span', 'perfilComp:idPais')
        self.idioma                 = self.find_text_by_id(soup, 'span', 'perfilComp:menuTipoIdioma')
        self.email                  = self.find_text_by_id(soup, 'span', 'perfilComp:idMail')
        self.nif                    = self.find_text_by_id(soup, 'span', 'perfilComp:idNumDoc')
        self.web                    = self.find_text_by_id(soup, 'span', 'perfilComp:textSSite__')
        self.actividad              = self.find_text_by_id(soup, 'span', 'perfilComp:idActividades')
        self.via                    = self.find_text_by_id(soup, 'span', 'perfilComp:idVia')
        self.codigo_postal          = self.find_text_by_id(soup, 'span', 'perfilComp:idCP')
        self.poblacion              = self.find_text_by_id(soup, 'span', 'perfilComp:idPoblac')
        self.prefijo                = self.find_text_by_id(soup, 'span', 'perfilComp:idTlfPrefijo')
        self.telefono               = self.get_phone_or_fax(soup, 'phone')
        self.fax                    = self.get_phone_or_fax(soup, 'fax')
        self.store()
        #...

    def find_text_by_id(self, soup, element, id_text):
        item = soup.find(element, id=re.compile(id_text))
        return item.get_text() if item else ''

    def get_url(self, soup):
        try:
            item = soup.find('a', id=re.compile('URLgenera'))
            return item['href']
        except TypeError:
            print('Error parsing url of organization with name: ' + self.nombre)
            return ""

    def get_phone_or_fax(self, soup, search):
        try:
            id_text = ""
            if search == 'phone':
                id_text = 'perfilComp:idTlf'
            elif search == 'fax':
                id_text = 'perfilComp:idFax'
            else:
                return ''

            item = soup.findAll('span', id=re.compile(id_text))
            return item[1].get_text() if item else ''
        except:
            return ""

    def is_valid(self):
        return bool(self.nombre)

    def store(self):

        if(not self.is_valid()):
            print('Organization not valid')
            return
        
        data = {
            'sourceUrl':    self.url_fuente,
            'linkUrl':      self.enlace,
            'name':         self.nombre,
            'country':      self.pais,
            'languages':    self.idioma,
            'email':        self.email,
            'nif':          self.nif,
            'webUrl':       self.web,
            'activity':     self.actividad,
            'street':       self.via,
            'postalCode':   self.codigo_postal,
            'town':         self.poblacion,
            'prefix':       self.prefijo,
            'phone':        self.telefono,
            'fax':          self.fax
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key" : os.environ["TENDIOS_API_KEY"]
        }

        response = requests.post(os.environ["TENDIOS_API_URL"]+'/v1/organizations', headers=headers, json=data)

        print("Status Code", response.status_code)