import sys
import re
import os
import bugsnag
import requests
import datetime

sys.path.append("../../../../utils")
sys.path.append("../../../../")

from driver import *

# Consultas Preliminares Plataforma de Contratación del Sector Público
class CP:

    def __init__(self, url, soup):

        if(not soup):
            soup = get_soup_from_url(url, 'html.parser')

        # ...
        self.url_fuente                                     = self.find_url(soup, "a", "URLgenera")
        self.enlace                                         = self.url_fuente
        self.consulta                                       = self.find_text_by_id(soup, 'span', 'text_Consulta')
        self.organo_de_contratacion                         = self.find_text_by_id(soup, 'span', 'text_OC_sin')
        self.estado                                         = self.find_text_by_id(soup, 'span', 'text_Estado')
        self.objeto_de_la_consulta                          = self.find_text_by_id(soup, 'span', 'text_ObjetoContrato')
        self.fecha_de_publicación                           = self.repair_publication_date(self.find_text_by_id(soup, 'span', 'text_fechaPub'))
        self.fecha_de_inicio_de_la_consulta                 = self.find_text_by_id(soup, 'span', 'text_fechainicio')
        self.fecha_limite_de_respuesta                      = self.find_text_by_id(soup, 'span', 'text_fechalimite')
        self.consulta_abierta                               = self.find_text_by_id(soup, 'span', 'text_abierta')
        self.participantes_en_la_consulta                   = self.find_text_by_id(soup, 'span', 'text_participantes')
        self.motivacion_en_la_seleccion_de_participantes    = self.find_text_by_id(soup, 'span', 'text_motivacion')
        self.direccion_internet_para_la_presentacion        = self.find_text_by_id(soup, 'span', 'text_dir')
        self.informacion_sobre_las_condiciones              = self.find_text_by_id(soup, 'span', 'text_info')
        self.idioma                                         = self.find_text_by_id(soup, 'span', 'text_idioma')
        self.objeto_del_contrato                            = self.find_text_by_id(soup, 'span', 'text_objetoContrato')
        if(self.objeto_del_contrato == ''):
            self.objeto_del_contrato                        = self.find_text_by_id(soup, 'span', 'textobjetoLic')
        self.tipo_de_contrato                               = self.find_text_by_id(soup, 'span', 'text_tipoContrato')
        self.procedimiento_de_contratacion                  = self.find_text_by_id(soup, 'span', 'text_procedimiento')
        self.codigos_cpv                                    = self.find_text_by_id(soup, 'span', 'text_CPV')
        self.fecha_creacion_expediente                      = self.find_date_from_table(soup)
        self.fecha_actualizacion_expediente                 = self.fecha_creacion_expediente
        self.documents                                      = self.find_documents(soup)
        self.sheets                                         = self.get_sheets()
        self.store()
        # ...

    def find_text_by_id(self, soup, element, id_text):
        item = soup.find(element, id=re.compile(id_text))
        return item.get_text() if item else ''

    def find_url(self, soup, element, id_text):
        item = soup.find(element, id=re.compile(id_text))
        return item['href'] if item else ''
    
    def repair_publication_date(self, date):
        parts = date.split(' ')
        parts1 = parts[0].split('-')

        return parts1[2] + '/' + parts1[1] + '/' + parts1[0] + ' ' + parts[1]
    
    def find_text_by_element_text(self, soup, element, attribute_name, attribute_text):
        item = soup.select_one(element+'['+attribute_name+'*="'+attribute_text+'"]')
        return item.get_text() if item else ''
    
    def find_documents(self, soup):
        table1 = self.find_documents_main_table(soup)
        table2 = self.find_documents_other_table(soup)
        return table1 + table2
    
    def find_documents_main_table(self, soup):
        items = []
        table = soup.find('table', id=re.compile("myTablaDetalleVISUOE_Anulados1"))

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
            if(document['name'] == 'Publicación'):
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
            if not link['href'].startswith('#'):
                sheet = {
                    'name': link.get_text(),
                    'url': link['href']
                }
                sheets.append(sheet)

        return sheets
    
    def find_date_from_table(self, soup):
        try:
            items = soup.find_all('td', {'class': 'fechaPubLeft'})
            return str(items[0].text)

        except:
            return ''
        
    def notify_error(self, bugsnagMessage, errorMessage, severity):
        try:
            if os.environ['ENVIRONMENT'] == 'production':
                bugsnag.notify(Exception(bugsnagMessage), severity=severity)
            else:
                print(errorMessage)
        except:
            print(errorMessage)

    def is_valid(self):
        return bool(self.consulta)

    def store(self):

        if(not self.is_valid()):
            print('consultation not valid')
            return

        data = {
            'sourceUrl':                self.url_fuente,
            'linkUrl':                  self.enlace,
            'expedient':                self.consulta,
            'contractingOrganization':  self.organo_de_contratacion,
            'status':                   self.estado,
            'consultationName':         self.objeto_de_la_consulta,
            'consultationCreatedAt':    self.fecha_de_publicación,
            'consultationStartDate':    self.fecha_de_inicio_de_la_consulta,
            'consultationDeadline':     self.fecha_limite_de_respuesta,
            'consultationOpen':         self.consulta_abierta,
            'participants':             self.participantes_en_la_consulta,
            'selectionType':            self.motivacion_en_la_seleccion_de_participantes,
            'webUrl':                   self.direccion_internet_para_la_presentacion,
            'conditions':               self.informacion_sobre_las_condiciones,
            'language':                 self.idioma,
            'expedientName':            self.objeto_del_contrato,
            'expedientContractType':    self.tipo_de_contrato,
            'expedientProcedure':       self.procedimiento_de_contratacion,
            'cpvCodes':                 self.codigos_cpv,
            'documents':                self.documents,
            # 'sheets':                   self.sheets,
            'expedientCreatedAt':       self.fecha_creacion_expediente,
            'expedientUpdatedAt':       self.fecha_actualizacion_expediente,
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key" : os.environ["TENDIOS_API_KEY"]
        }

        response = requests.post(os.environ["TENDIOS_API_URL"]+'/v1/tenders/source/consultas/create', headers=headers, json=data)

        print("Status Code", response.status_code)