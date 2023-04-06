import sys
import requests
import re
import json
import os
import bugsnag
import asyncio

sys.path.append("../../../../utils")
sys.path.append("../../../../")

from driver import *
from tokenizer import *
from location_db import *
from functions import *

# Licitacion Diário da República Electrónico
class LDRE:

    def __init__ (self, url, soup, match):
        
        if(not soup):
            # clickFirst argument is not necessary for this site
            soup = get_soup_dynamic_webpage(url = url, ecx = '//div[@id="b7-b8-InjectHTMLWrapper"]') # ecx might vary in time in dre
            try:
                fields = soup.find_all("p")
            except AttributeError:
                fields = None
                while fields == None:
                    print("No fields found")
                    soup = get_soup_dynamic_webpage(url = url, ecx = '//div[@id="b7-b8-InjectHTMLWrapper"]')
                    fields = soup.find_all("p")

            for field in fields:
                fields[fields.index(field)] = field.get_text(strip=True)

        locationRepository = JSONLocationRepository("../../../../location.json")
        tenderInformation = self.populateDic(fields, url)

        #...
        self.url_fuente                                         = url
        self.enlace                                             = url
        self.expediente                                         = tenderInformation["expediente"]
        # self.ubicacion_organica                                 = self.find_text_by_id(soup, "span", "text_UbicacionOrganica")
        self.organo_de_contratacion                             = tenderInformation["organo_contratacion"]
        # self.estado_de_la_licitación                            = self.find_text_by_id(soup, "span", "text_Estado")
        self.objeto_del_contrato                                = tenderInformation["objeto"]
        self.presupuesto_base_de_licitacion_sin_impuestos       = tenderInformation["presupuesto_base"]
        self.valor_estimado_del_contrato                        = tenderInformation["valor_estimado"]
        self.tipo_de_contrato                                   = tenderInformation["tipo_contrato"]
        self.codigo_cpv                                         = tenderInformation["cpv"]
        self.lugar_de_ejecucion                                 = tenderInformation["locationText"]
        if(self.lugar_de_ejecucion != None):
            self.lugar                                          = self.get_location(locationRepository, tokenize(self.lugar_de_ejecucion))
        else:
            self.lugar                                          = None
        self.parentTenderId                                     = tenderInformation["parent_id"]
        # self.procedimiento_de_contratacion                      = self.find_text_by_id(soup, "span", "text_Procedimiento")
        # self.fecha_fin_de_presentación_de_oferta                = self.find_text_by_id(soup, "span", "text_FechaPresentacionOfertaConHora")
        self.fecha_de_publicacion_del_expediente                = self.find_publication_date(soup)
        self.fecha_de_actualizacion_del_expediente              = self.fecha_de_publicacion_del_expediente
        # self.resultado                                          = self.find_text_by_id(soup, "span", "text_Resultado")
        # self.adjudicatario                                      = self.find_text_by_id(soup, "span", "text_Adjudicatario")
        # self.numero_licitadores                                 = self.find_text_by_id(soup, "span", "text_NumeroLicitadores")
        # self.importe_adjudicacion                               = self.find_text_by_id(soup, "span", "text_ImporteAdjudicacion")
        # self.documents                                          = self.find_documents(soup)
        # self.sheets                                             = self.get_sheets()
        self.match                                              = match
        # #...
        save_html(soup, self.expediente)
        self.store()


    def populateDic(self, fields, url):
        try:
            info = {}
            info["expediente"] = fields[-1]

            for field in fields:
                if "Número de referência interna" in field:
                    info["expediente"] = field.split("interna: ")[1]

                elif "retificação" in field:
                    info["parent_id"] = field.split("ID ")[1][:-1]

                elif "Designação da entidade adjudicante" in field:
                    info["organo_contratacion"] = field.split("adjudicante: ")[1]
                
                elif "Entidade contraente" in field:
                    info["organo_contratacion"] = field.split("contraente: ")[1]

                elif "Designação do contrato" in field:
                    info["objeto"] = field.split("contrato: ")[1]

                elif "Objeto do contrato a celebrar" in field:
                    info["objeto"] = field.split("celebrar: ")[1]

                elif "Vocabulário principal" in field:
                    info["cpv"] = field.split("principal: ")[1]
                
                elif "Tipo de Contrato Principal" in field:
                    info["tipo_contrato"] = field.split("Principal: ")[1]

                elif "Valor do preço base do procedimento" in field:
                    info["presupuesto_base"] = field.split("procedimento: ")[1][:-4]
                
                elif re.sub('[^a-zA-Z]+', '', field)[:-3] == "Valor": # and "Valor do preço base do procedimento" not in field and "Sim" not in field:
                    info["valor_estimado"] = field.split("Valor: ")[1][:-4]

                elif "NUT" in field:
                    info["locationText"] = field.split(": ")[1]

            # In case info was not found we return empty value
            if "parent_id" not in info:
                info["parent_id"] = None

            if "cpv" not in info:
                info["cpv"] = ""

            if "tipo_contrato" not in info:
                info["tipo_contrato"] = "no definido"

            if "presupuesto_base" not in info:
                info["presupuesto_base"] = None

            if "valor_estimado" not in info:
                info["valor_estimado"] = None

            if "locationText" not in info:
                info["locationText"] = None
            
            if "organo_contratacion" not in info:
                info["organo_contratacion"] = None

            if "objeto" not in info:
                info["objeto"] = None

            return info
        except:
            self.notify_error('DRE: Error populating dictionary', "ERROR!!!\n---------------------\nURL:" + url + "\nError populating dictionary", "error")


    def find_publication_date(self, soup):
        field = soup.select('span:-soup-contains("Data de Publicação") + a')
        return self.format_date(field[0].text)

    def format_date(self, date):
        date = date.replace("-", "")
        indx = [0,4,6]
        parts = [date[i:j] for i,j in zip(indx, indx[1:]+[None])]
        formatted_date = parts[2] + "/" + parts[1] + "/" + parts[0]
        return formatted_date

    def get_location(self, locationRepo, tokens):
        locations = asyncio.run(locationRepo.getLocationFromTokens(tokens))
        return locations

    def notify_error(self, bugsnagMessage, errorMessage, severity):
        try:
            if os.environ['ENVIRONMENT'] == 'production':
                bugsnag.notify(Exception(bugsnagMessage), severity=severity)
            else:
                print(errorMessage)
        except:
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
            # 'status':                       self.estado_de_la_licitación,
            'sourceUrl':                    self.url_fuente,
            'linkUrl':                      self.enlace,
            'locationText':                 self.lugar_de_ejecucion,
            'locations':                    self.lugar,
            'parentTenderId':               self.parentTenderId,
            # 'submissionDeadlineDate':       self.fecha_fin_de_presentación_de_oferta,
            'expedientCreatedAt':           self.fecha_de_publicacion_del_expediente,
            'expedientUpdatedAt':           self.fecha_de_actualizacion_del_expediente,
            # 'procedure':                    self.procedimiento_de_contratacion,
            'contractingOrganization':      self.organo_de_contratacion,
            'budgetNoTaxes':                self.presupuesto_base_de_licitacion_sin_impuestos,
            'contractEstimatedValue':       self.valor_estimado_del_contrato,
            # 'result':                       self.resultado,
            # 'successBidderOrganization':    self.adjudicatario,
            # 'biddersNumber':                self.numero_licitadores,
            # 'awardAmount':                  self.importe_adjudicacion,
            # 'documents':                    self.documents,
            # 'sheets':                       self.sheets,
            'match':                        self.match
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key" : os.environ["TENDIOS_API_KEY"]
        }

        response = requests.post(os.environ["TENDIOS_API_URL"]+'/v1/tenders/source/dre/create', headers=headers, json=data)

        print("Status Code", response.status_code)