import sys
import requests
import re
import json
import os
import time
import asyncio
import bugsnag
from selenium.webdriver.common.by import By

sys.path.append("../../../../utils")
sys.path.append("../../../../")

from driver import *
from tokenizer import *
from location_db import *
from functions import *

# Licitacion TED
class LTED:

    def __init__ (self, url, soup, match):
        if(not soup):
            soup = get_soup_from_url(url, "html.parser")
        
        self.locationRepository = JSONLocationRepository("../../../../location.json")

        # Case ted returns an error page
        if bool(soup.body.findAll(text="Error page")):
            return

        #...
        self.url_fuente                                         = url
        self.enlace                                             = url # Cambiar por url pdf
        self.expediente                                         = self.get_expedient(soup)
        self.moneda                                             = ""
        # self.ubicacion_organica                                 = self.find_text_by_id(soup, "span", "text_UbicacionOrganica")
        self.organo_de_contratacion                             = self.get_contractingOrganization(soup)
        self.objeto_del_contrato                                = self.get_name(soup)
        self.presupuesto_base_de_licitacion_sin_impuestos       = self.get_budgetNoTaxes(soup)
        # self.valor_estimado_del_contrato                        = self.find_text_by_id(soup, "span", "text_ValorContrato")
        self.codigo_cpv                                         = self.find_cpv_codes(soup, "span", "class", "cpvCode")
        # self.fecha_fin_de_presentación_de_oferta                = self.find_text_by_id(soup, "span", "text_FechaPresentacionOfertaConHora")
        # self.resultado                                          = self.find_text_by_id(soup, "span", "text_Resultado")
        self.adjudicatario                                      = self.get_successBidderOrganization(soup)
        self.numero_licitadores                                 = self.get_biddersNumber(soup)
        self.importe_adjudicacion                               = self.get_awardAmount(soup)
        # self.documents                                          = self.find_documents(soup)
        # self.sheets                                             = self.get_sheets()

        dataBtnXPath                                            = self.get_button_xpath(soup, 'Datos')
        pageSoup                                                = self.switch_to_page(dataBtnXPath) 
        self.estado_de_la_licitación                            = self.get_status(pageSoup)
        self.lugar_de_ejecucion                                 = self.get_dataPage_info(pageSoup, "LugarEjecucion")
        self.lugar                                              = self.get_locationNuts(self.locationRepository, tokenize(self.lugar_de_ejecucion))
        self.correct_location()
        self.tipo_de_contrato                                   = self.get_dataPage_info(pageSoup, "TipoContrato")
        self.procedimiento_de_contratacion                      = self.get_dataPage_info(pageSoup, "TipoProcedimiento")
        self.fecha_de_publicacion_del_expediente                = self.get_dataPage_info(pageSoup, "FechaPublicacion")
        self.fecha_de_actualizacion_del_expediente              = self.fecha_de_publicacion_del_expediente

        self.parentTenderId                                     = ""
        if bool(soup.select('a:-soup-contains("Documentos relacionados")')):
            relationsButtonXpath                                    = self.get_button_xpath(pageSoup, "Documentos relacionados")
            pageSoup                                                = self.switch_to_page(relationsButtonXpath)
            self.parentTenderId                                     = self.get_parent_tender_id(pageSoup)
        #...
        self.match                                              = match
        save_html(soup, self.expediente)
        self.store()

    def correct_location(self):
        if not self.lugar:
            maxTrials = len(self.lugar_de_ejecucion)
            trials = 0
            while not self.lugar and trials <= maxTrials:
                self.lugar = self.get_locationNuts(self.locationRepository, tokenize(self.lugar_de_ejecucion[:-trials]))
                trials += 1

    def switch_to_page(self, xpath):
        driver = get_driver_from_url(self.url_fuente)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element(By.XPATH, xpath).click()
        soup = get_soup_from_driver(driver, "html.parser")
        driver.quit()
        return soup

    def get_expedient(self,soup):
        try:
            item = soup.find_all(text = re.compile("Número de referencia"))
            if item:
                item = soup.find_all(text = re.compile("Número de referencia"))[0].text.split(":")[1]

                if item == "":
                    item = soup.select('span:-soup-contains("Número de referencia") + div')
                    for span in item:
                        item = span.text

                return item
            
            else:
                item = soup.find("h2", {"id": "page-title"}).text.split("- ")[1]

            return item
        except:
            self.notify_error('TED: Error parsing expedient from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: EXPEDIENT", "error")
            return ""

    def get_contractingOrganization(self, soup):
        try:
            item = soup.find_all(text = re.compile("Nombre oficial: "))[0].split("Nombre oficial: ")[1]
            return item
        except:
            # self.notify_error('TED: Error parsing Contracting Organization from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: Contracting Organization", "warning") 
            return ""

    def get_name(self, soup):
        try:
            element = ""
            for e in soup.select('span:-soup-contains("Denominación") + div'):
                element = element + " " + e.get_text(strip=True)
            return element
        except:
            self.notify_error('TED: Error parsing Name from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: NAME", "error")
            return ""

    def find_cpv_codes(self, soup, element, attribute_name, attribute_text):
        try:
            codes = ""
            item = soup.select(element+'['+attribute_name+'*="'+attribute_text+'"]')
            for code in item:
                codes = codes + code.get_text() + ","
        
            return codes[:-1]
        except:
            # self.notify_error('TED: Error parsing CPV Codes from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: CPV Codes", "warning")
            return ""

    # self.find_element_text(contenedor, "h1", "class", "notranslate")
    def find_text_by_id(self, soup, element, id_text):
        item = soup.find(element, id=re.compile(id_text))
        return item.get_text() if item else ''

    def find_text_by_element_text(self, soup, element, attribute_name, attribute_text):
        item = soup.select_one(element+'['+attribute_name+'*="'+attribute_text+'"]')
        return item.get_text() if item else ''

    def get_status(self, soup):
        try:
            field = soup.select('td:-soup-contains("Tipo de anuncio") + td')[0].text
            text = field.split("- ")[1].strip()
            if text == "Anuncio de adjudicación de contrato":
                status = "Adjudicada"
            elif text == "Anuncio de licitación":
                status = "Publicada"
            else:
                status = "No definido"
            return status
        except:
            self.notify_error('TED: Error parsing Status from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: STATUS", "error")
            return ""

    def get_contract_type(self, soup):
        try:
            field = soup.select('td:-soup-contains("Tipo de contrato") + td')
            return field[0].text.strip("4 -").strip()
        except:
            self.notify_error('TED: Error parsing Contract Type from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: CONTRACT TYPE", "error")
            return ""

    def get_location(self, soup):
        try:
            field = soup.select('td:-soup-contains("Lugar de ejecución") + td')
            text = field[0].text
            return text
        except:
            # self.notify_error('TED: Error parsing Location from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: LOCATION", "warning")
            return ""

    def get_dataPage_info(self, soup, info):
        if info == "TipoContrato":
            searchText = "Tipo de contrato"
        elif info == "LugarEjecucion":
            searchText = "Lugar de ejecución"
        elif info == "TipoProcedimiento":
            searchText = "Tipo de procedimiento"
        elif info == "FechaPublicacion":
            searchText = "Fecha de publicación"

        try:
            field = soup.select(f'td:-soup-contains("{searchText}") + td')

            if info == "LugarEjecucion" or info == "FechaPublicacion":
                return field[0].text
            return field[0].text[3:].strip()
        except:
            self.notify_error('TED: Error parsing' + searchText + 'from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: " + searchText, "error")
            return ""

    def get_locationNuts(self, locationRepo, tokens):
        locations = asyncio.run(locationRepo.getLocationFromTokens(tokens))
        return locations

    def get_button_xpath(self, soup, button):
        tabs = soup.find("ul", {"id": "notice-tabs"})
        dataIndex = 0
        index = 1
        for li in tabs:
            if len(li.text) != 1:
                if li.text.strip() == button:
                    dataIndex = index
                index += 1
        
        return "//ul[@id='notice-tabs']/li[" + str(dataIndex) + "]/a"

    def get_budgetNoTaxes(self, soup):
        try:
            field = soup.select('span:-soup-contains("Valor total de la contratación") + div')
            return field[0].text.split(": ")[1][:-4].replace(" ", "")
        except:
            try:
                field = soup.select('span:-soup-contains("Valor total estimado") + div')
                return field[0].text.split(": ")[1][:-4].replace(" ", "")
            except:
                # self.notify_error('TED: Error parsing Budget No Taxes from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: BUDGET NO TAXES", "warning")
                return None

    # Gets all information about successBidderOrganization. Right now only returns the name because is the only information we want, but we could get more from info
    def get_successBidderOrganization(self, soup):
        try:
            info = {}
            tmp = ""
            field = soup.select('span:-soup-contains("Nombre y dirección del contratista") + div')
            for child in field[0].children:

                if not child.text == '':
                    if child.text.endswith(': '):
                        tmp = child.text
                    else:
                        string_tmp = tmp + child.text
                        list_tmp = string_tmp.split(': ')
                        info[list_tmp[0]] = list_tmp[1]

            # Info contains all information about the organization, right now we only want the name, but if needed we can retrieve more
            return info['Nombre oficial']

        except Exception:
            # self.notify_error('TED: Error parsing Success Bidder Organization from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: SUCCESS BIDDER ORGANIZATION", "warning")
            return None

    def get_biddersNumber(self, soup):
        try:
            field = soup.find_all(text = re.compile("Número de ofertas recibidas:"))
            return str(re.sub("[^0-9]", "", field[0].text))
        except:
            # self.notify_error('TED: Error parsing Bidders Number from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: BIDDERS NUMBER", "warning")
            return None

    def get_awardAmount(self, soup):
        try:
            field = soup.find_all(text = re.compile("Valor total del contrato"))
            info = field[0].text.split(": ")[1]
            amount = info[:-4].replace(" ", "")


            currency = re.sub('[^a-zA-Z]+', '', info)
            if currency == 'GBP':
                self.moneda = 'British Pound'
            else:
                self.moneda = 'Euro'
            return amount
        except:
            # self.notify_error('TED: Error parsing Award Amount from ' + self.url_fuente, "ERROR!!!\n---------------------\nURL:" + self.url_fuente + "\nError scraping: AWARD AMOUNT", "warning")
            return None

    def get_parent_tender_id(self, soup):
        field = soup.find('table', 'family')
        parent_id = field.find('a').text.split(':')[0]
        return parent_id

    def notify_error(self, bugsnagMessage, errorMessage, severity):
        try:
            if os.environ['ENVIRONMENT'] == 'production':
                bugsnag.notify(Exception(bugsnagMessage), severity=severity)
            else:
                print(errorMessage)
        except:
            print(errorMessage)

    def is_valid(self):
        return bool(self.expediente) and bool(self.objeto_del_contrato) and bool(self.estado_de_la_licitación)

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
            # 'submissionDeadlineDate':       self.fecha_fin_de_presentación_de_oferta,
            'expedientCreatedAt':           self.fecha_de_publicacion_del_expediente,
            'expedientUpdatedAt':           self.fecha_de_actualizacion_del_expediente,
            'procedure':                    self.procedimiento_de_contratacion,
            'contractingOrganization':      self.organo_de_contratacion,
            'budgetNoTaxes':                self.presupuesto_base_de_licitacion_sin_impuestos,
            # 'contractEstimatedValue':       self.valor_estimado_del_contrato,
            # 'result':                       self.resultado,
            'successBidderOrganization':    self.adjudicatario,
            'biddersNumber':                self.numero_licitadores,
            'awardAmount':                  self.importe_adjudicacion,
            # 'documents':                    self.documents,
            # 'sheets':                       self.sheets,
            'currency':                     self.moneda,
            'parentTenderId':               self.parentTenderId,
            'match':                        self.match
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key" : os.environ["TENDIOS_API_KEY"]
        }

        response = requests.post(os.environ["TENDIOS_API_URL"]+'/v1/tenders/source/ted/create', headers=headers, json=data)

        print("Status Code", response.status_code)