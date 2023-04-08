import sys
import requests
import re
import json
import os
import asyncio
import bugsnag

sys.path.append("../../utils")
sys.path.append("../../")

from driver import *
from tokenizer import *
from location_db import *
from functions import *

from datetime import datetime

# Licitacion Contrataciones Menores
class LCM:

    def __init__ (self, url, soup, match):

        if(not soup):
            soup = get_soup_from_url(url, "html.parser")

        locationRepository = JSONLocationRepository("../../location.json")

        dates = self.find_dates_from_table(soup)

        #...
        self.url_fuente                                         = self.find_url(soup, "a", "URLgenera")
        self.enlace                                             = self.url_fuente
        self.expediente                                         = self.must_find_text_by_id(soup, "span", "text_Expediente")
        # self.ubicacion_organica                                 = self.find_text_by_id(soup, "span", "text_UbicacionOrganica")
        self.organo_de_contratacion                             = self.find_text_by_id(soup, "span", "text_OC_con")
        self.estado_de_la_licitación                            = self.must_find_text_by_id(soup, "span", "text_Estado")
        self.objeto_del_contrato                                = self.must_find_text_by_id(soup, "span", "text_ObjetoContrato")
        self.presupuesto_base_de_licitacion_sin_impuestos       = self.find_text_by_id(soup, "span", "text_Presupuesto")
        self.valor_estimado_del_contrato                        = self.find_text_by_id(soup, "span", "text_ValorContrato")
        self.tipo_de_contrato                                   = self.must_find_text_by_id(soup, "span", "text_TipoContrato")
        self.codigo_cpv                                         = self.find_text_by_id(soup, "span", "text_CPV")
        self.lugar_de_ejecucion                                 = self.find_text_by_id(soup, "span", "text_LugarEjecucion")
        self.lugar                                              = self.get_location(locationRepository, tokenize(self.lugar_de_ejecucion))
        self.procedimiento_de_contratacion                      = self.must_find_text_by_id(soup, "span", "text_Procedimiento")
        self.fecha_fin_de_presentación_de_oferta                = self.find_text_by_id(soup, "span", "text_FechaPresentacionOfertaConHora")
        self.fecha_de_publicacion_del_expediente                = dates[0]
        self.fecha_de_actualizacion_del_expediente              = self.find_text_by_id(soup, "span", "text_FechaActualizacion")
        if self.fecha_de_actualizacion_del_expediente == '':
            self.fecha_de_actualizacion_del_expediente          = dates[1]
        # self.resultado                                          = self.find_text_by_id(soup, "span", "text_Resultado")
        # self.adjudicatario                                      = self.find_text_by_id(soup, "span", "text_Adjudicatario")
        # self.numero_licitadores                                 = self.find_text_by_id(soup, "span", "text_NumeroLicitadores")
        # self.importe_adjudicacion                               = self.find_text_by_id(soup, "span", "text_ImporteAdjudicacion")
        self.documents                                          = self.find_documents(soup)
        self.sheets                                             = self.get_sheets()
        #...
        self.store()

    def must_find_text_by_id(self, soup, element, id_text):
        try:
            item = soup.find(element, id=re.compile(id_text))
            return item.get_text()
        except:
            self.notify_error('Contrataciones Menores: Error parsing element ' + id_text + ' from url ' + self.url_fuente)
            return ''

    def find_text_by_id(self, soup, element, id_text):
        try:
            item = soup.find(element, id=re.compile(id_text))
            return item.get_text()
        except:
            return ''

    def find_url(self, soup, element, id_text):
        item = soup.find(element, id=re.compile(id_text))
        return item['href'] if item else ''

    def get_location(self, locationRepo, tokens):
        locations = asyncio.run(locationRepo.getLocationFromTokens(tokens))
        return locations

    # self.find_element_text(contenedor, "h1", "class", "notranslate")
    def find_text_by_element_text(self, soup, element, attribute_name, attribute_text):
        item = soup.select_one(element+'['+attribute_name+'*="'+attribute_text+'"]')
        return item.get_text() if item else ''

    def find_dates_from_table(self, soup):
        try:
            items = soup.find_all('td', {'class': 'fechaPubLeft'})
            firstTime = True
            for item in items:
                date = datetime.strptime(item.text[:6] + item.text[8:], '%d/%m/%y %H:%M:%S')

                if firstTime:
                    lastUpdate = date
                    firstUpdate = date
                    firstTime = False

                if date < firstUpdate:
                    firstUpdate = date

                if date > lastUpdate:
                    lastUpdate = date

            return [self.format_date(str(firstUpdate)), self.format_date(str(lastUpdate))]
        except:
            return ''

    def format_date(self, date):
        indx = [0,4,7,10,13,16]
        parts = [date[i:j] for i,j in zip(indx, indx[1:]+[None])]
        for idx, el in enumerate(parts):
            parts[idx] = el.replace('-','').replace(':','').replace(' ','')
        
        return parts[2] + '/' + parts[1] + '/' + parts[0] + ' ' + parts[3] + ':' + parts[4] + ':' + parts[5]

    def find_documents(self, soup):
        table1 = self.find_documents_main_table(soup)
        table2 = self.find_documents_other_table(soup)
        return table1 + table2

    def find_documents_main_table(self, soup):
        items = []
        table = soup.find('table', id=re.compile("myTablaDetalleVISUOE"))

        # check if table exists
        if(table is None):
            return items

        # iterate for all rows
        rows = table.find('tbody').findAll('tr')
        for row in rows:
            item = {
                'publicationDate': self.find_text_by_element_text(row, "td", "class", "fechaPubLeft"),
                'name': self.find_text_by_element_text(row, "td", "class", "tipoDocumento"),
                'documents': self.get_documents(row)
            }
            items.append(item)

        return items

    def find_documents_other_table(self, soup):
        items = []
        table = soup.find('table', id=re.compile("TableEx1_Aux"))

        # check if table exists
        if(table is None):
            return items

        # iterate for all rows
        rows = table.find('tbody').select('tr[class*="rowClass"]')
        for row in rows:
            new_row = row.find('tr')
            item = {
                'publicationDate': self.find_text_by_element_text(new_row, "span", "id", "textSfecha1PadreGen"),
                'name': self.find_text_by_element_text(new_row, "span", "id", "textStipo1PadreGen"),
                'documents': self.get_documents(new_row)
            }
            items.append(item)

        return items    
    
    def get_documents(self, row):
        documents = []
        tds = row.select('td')

        for td in tds:
            if(td is None):
                return documents

            links = td.findAll('a', href=True)
            for link in links:

                href = link['href']

                if(href == '#'):
                    continue

                document = {
                    'name': link.get_text(),
                    'url': href
                }
                documents.append(document)

        return documents

    def get_sheets(self):
        sheets = []
        for document in self.documents:
            if(document['name'] == 'Pliego' or document['name'] == 'Rectificación de Pliego'):
                for link in document['documents']:
                    if(link['name'] == 'Html'):
                        sheets = self.find_sheets(link['url'])
        return sheets

    def find_sheets(self, url):
        sheets = []
        soup = get_soup_from_url(url, "html.parser")
        box = soup.select_one('div[class*="boxWithBackground"]')

        if(box is None):
            return sheets

        links = box.findAll('a', href=True)
        for link in links:

            sheet = {
                'name': link.get_text(),
                'url': link['href']
            }
            sheets.append(sheet)

        return sheets

    def notify_error(self, errorMessage):
        print(errorMessage)

    def is_valid(self):
        return bool(self.expediente) and bool(self.objeto_del_contrato) # and bool(self.estado_de_la_licitación)

    def store(self):

        if(not self.is_valid()):
            print('tender not valid')
            return

        data = {
            'expedient':                    self.expediente,
            'name':                         self.objeto_del_contrato,
            'contractType':                 self.tipo_de_contrato,
            'cpvCodes':                     self.codigo_cpv,
            'status':                       self.estado_de_la_licitación,
            'sourceUrl':                    self.url_fuente,
            'linkUrl':                      self.enlace,
            'locationText':                 self.lugar_de_ejecucion,
            'locations':                    self.lugar,
            'submissionDeadlineDate':       self.fecha_fin_de_presentación_de_oferta,
            'expedientCreatedAt':           self.fecha_de_publicacion_del_expediente,
            'expedientUpdatedAt':           self.fecha_de_actualizacion_del_expediente,
            'procedure':                    self.procedimiento_de_contratacion,
            'contractingOrganization':      self.organo_de_contratacion,
            'budgetNoTaxes':                self.presupuesto_base_de_licitacion_sin_impuestos,
            'contractEstimatedValue':       self.valor_estimado_del_contrato,
            # 'result':                       self.resultado,
            # 'successBidderOrganization':    self.adjudicatario,
            # 'biddersNumber':                self.numero_licitadores,
            # 'awardAmount':                  self.importe_adjudicacion,
            'documents':                    self.documents,
            'sheets':                       self.sheets,
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key" : os.environ["API_KEY"]
        }

        response = requests.post(os.environ["API_URL"]+'/v1/tenders/source/contratacionesmenores/create', headers=headers, json=data)

        print("Status Code", response.status_code)