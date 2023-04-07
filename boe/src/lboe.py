import sys
import requests
import re
import os
import asyncio
import bugsnag

sys.path.append("../../utils")
sys.path.append("../../")

from driver import *
from tokenizer import *
from location_db import *
from functions import *

# Licitacion Boletín Oficial del Estado

class LBOE:

    def __init__(self, url, match):
        soup = get_soup_from_url(url, "lxml")

        locationRepository = JSONLocationRepository("../../location.json")
        titulo = self.find_text_by_tag(soup, "titulo")
        
        # ...
        self.url_fuente                                          = url
        self.enlace                                              = "https://www.boe.es" + self.find_text_by_tag(soup, "url_pdf")
        self.expediente                                          = self.get_element_from_title(soup, "expediente", titulo)
        #self.ubicacion_organica                                 = self.find_text_by_id(soup, "span", "text_UbicacionOrganica")
        self.organo_de_contratacion                              = self.get_element_from_title(soup, "adjudicador", titulo)
        self.estado_de_la_licitación                             = self.get_status(soup)
        self.objeto_del_contrato                                 = self.get_element_from_title(soup, "objeto", titulo)
        #self.presupuesto_base_de_licitacion_sin_impuestos       = self.find_text_by_id(soup, "span", "text_Presupuesto")
        self.valor_estimado_del_contrato                         = self.get_contract_value(soup)
        #self.tipo_de_contrato                                   = self.find_text_by_id(soup, "span", "text_TipoContrato") //añadir bugsnag
        self.codigo_cpv                                          = self.get_cpv_codes(soup)
        self.lugar_de_ejecucion                                  = self.get_location_codes(soup)
        self.lugar                                               = self.get_location(locationRepository, tokenize(self.lugar_de_ejecucion))
        self.adjudicatarios                                      = self.get_data(soup, "adjudicatarios")
        self.procedimiento_de_contratacion                       = self.get_data(soup, "tipo_procedimiento")
        #self.fecha_fin_de_presentación_de_oferta                = self.find_text_by_id(soup, "span", "text_FechaPresentacionOfertaConHora")
        self.fecha_de_publicacion_del_expediente                = self.format_boe_date(self.find_text_by_tag(soup, "fecha_publicacion"))
        self.fecha_de_actualizacion_del_expediente              = self.format_boe_date(self.find_field_in_tag(soup, "documento", "fecha_actualizacion"))
        #self.resultado                                          = self.find_text_by_id(soup, "span", "text_Resultado")
        #self.adjudicatario                                      = self.find_text_by_id(soup, "span", "text_Adjudicatario")
        self.numero_licitadores                                 = self.get_bidders_number(soup)
        #self.importe_adjudicacion                               = self.find_text_by_id(soup, "span", "text_ImporteAdjudicacion")
        #self.documents                                          = self.find_documents(soup)
        #self.sheets                                             = self.get_sheets()
        self.match                                              = match
        # ...
        self.store()

    def find_text_by_tag(self, soup, tag):
        item = soup.find(tag)
        return item.text if item else ''

    def find_field_in_tag(self, soup, tag, field):
        item = soup.find(tag)
        return item[field] if item else ''

    def format_boe_date(self, date):
        indx = [0,4,6,8,10,12]
        parts = [date[i:j] for i,j in zip(indx, indx[1:]+[None])]
        return parts[2] + '/' + parts[1] + '/' + parts[0] + ' ' + parts[3] + ':' + parts[4]

    def get_status(self, soup):
        try:
            text = self.find_text_by_tag(soup, "modalidad")
            if text == "Formalización contrato":
                return "Adjudicada"
            elif text == "Licitación":
                return "Publicada"
            else:
                return "No definido"
        except:
            self.notify_error('BOE: Error parsing Status from ' + self.url_fuente)
            return ""

    def get_cpv_codes(self, soup):
        try:
            codes = ""
            try:
                #Case more than one code in generic tag
                try:
                    # Get all XML included inside CPVCodes
                    data = list(soup.select_one('dt:-soup-contains("Códigos CPV:") + dd dl').stripped_strings)

                    # Create a dictionary with the codes as values and keep only the values (currently lists)
                    codesLists = {k.split(') ')[-1]:re.findall(r'\d{8}', v) for k, v in zip(data[::2], data[1::2])}.values()

                    # Format codesLists into a single String containing all codes
                    for codeList in codesLists:
                        for code in codeList:
                            if code not in codes:
                                codes += code + ","

                    # Delete last comma    
                    codes = codes[:-1]

                #Case only one code in generic tag
                except:
                    data = list(soup.select_one('dt:-soup-contains("Códigos CPV:") + dd').stripped_strings)
                    codes = data[0].split(" ")[0]

            #Case no code in generic tag
            except:
                materias_cpv = soup.find("materias_cpv").text
                #codes = re.findall(r'\d{8}', materias_cpv)
                codes = re.sub("[^0-9]", ",", materias_cpv)

            return codes
        except:
            return ""

    def get_data(self, soup, data):
        xml = ""
        values = []
        index = 0

        if(data == "adjudicatarios"):
            try:
                xml = list(soup.select_one('dt:-soup-contains("Adjudicatarios:") + dd dl').stripped_strings)

                for el in xml:
                    if "Nombre:" in el:
                        index = xml.index(el) + 1
                        values.append(xml[index])

                return ','.join(values) # return list of values on a string separated by , at the moment there have been no cases with more than one value, addapt rest of the code if it appears with more than one
            except:
                return None

        elif (data == "tipo_procedimiento"):
            try:
                try:
                    procedure = list(soup.select_one('dt:-soup-contains("Tipo de procedimiento") + dd').stripped_strings)

                    if "Tipo" in procedure[0]:
                        procedure = procedure[1][:-1]

                    else:
                        procedure = procedure[0][:-1]
                
                    if "Abierto acelerado" in procedure:
                        procedure = "Abierto acelerado"

                    if "(" in procedure:
                        procedure = procedure.split("(")[0][:-1]
                
                    return procedure

                # Tipo de procedimiento de adjudicación no aparece en el xml
                except AttributeError:
                    return "No definido"
            except:
                self.notify_error('BOE: Error parsing Procedure from ' + self.url_fuente)
                return "No definido"
        else:
            return ""

    def get_element_from_title(self, soup, element, title):
        # HACER UPDATE SI EL BOE CAMBIA EL FORMATO DE LAS LICITACIONES
        if "Expediente" not in title:
            xml = list(soup.find("texto").stripped_strings)

            if element == "expediente":
                try:
                    for el in xml:
                        if "Número de expediente: " in el:
                            expediente = el.split(": ")[1]
                            return expediente
                except:
                    self.notify_error('BOE: Error parsing Expedient from ' + self.url_fuente)
                    return ""

            elif element == "objeto":
                try:
                    return soup.find("titulo").text
                except:
                    self.notify_error('BOE: error parsing Name from ' + self.url_fuente)
                    return ""

        else:
            if element == "expediente":
                try:
                    # Expedientes se encuentran al final del título, han habido casos de expedientes entre parentesis y/o con puntos, por lo que no se puede hacer split("Expediente: ")[1].split(".")
                    expediente = title.split("Expediente")[1]

                    #Check if it contains ":" and delete it and clear first blank space
                    if ":" in expediente:
                        expediente.replace(":", "")
                        expediente = expediente[1:]
                    else:
                        expediente = expediente[1:]

                    #Check if it has parenthesis
                    parenthesis = False
                    if "(" in expediente or ")" in expediente:
                        parenthesis = True


                    if "." in expediente and expediente.endswith("."):
                        expediente = expediente[:-1]

                        if parenthesis:
                            expediente = expediente[:-1]
                    
                    return expediente
                except:
                    self.notify_error('BOE: Error parsing Expedient from ' + self.url_fuente)
                    return ""

            elif element == "objeto":
                try:
                    # Objeto suele aparecer como segundo elemento después del adjudicador antes del expediente, si no hay adjudicador es el primer elemento
                    try:
                        objeto = title.split("Objeto: ")[1].split("Expediente:")[0]

                        if objeto.endswith("("):
                            objeto = objeto[:-2]

                        return objeto
                
                    except:
                        objeto = title.split("Expediente")[0]

                        if objeto.endswith("("):
                            objeto = objeto[:-2]

                        return objeto
                except:
                    self.notify_error('BOE: error parsing Name from ' + self.url_fuente)
                    return ""

            elif element == "adjudicador":
                # Adjudicador suele ser el primer elemento del título, en los casos en los que no aparecía aquí podía aparecer en un tag texto dentro de un <p>
                try:
                    return title.split(". ")[0].split(": ")[1]
                except:
                    try:
                        xml = list(soup.find("texto").stripped_strings)

                        for el in xml:
                            if "Organismo:" in el :
                                organismo = el.split("Organismo: ")[1]
                                return organismo
                    except:
                        return ""
            else:
                return ""

    # Returns codes as a string separated by commas
    def get_location_codes(self, soup):
        case1 = False # case 1 https://i.imgur.com/iv6WueQ.png
        case2 = False # case 2 https://i.imgur.com/A9Xye2I.png

        # Case 0 https://i.imgur.com/8z8I549.png or "Lugar principal de ejecucion:"
        try:
            try:
                data = list(soup.select_one('dt:-soup-contains("Lugar principal de prestación de los servicios:") + dd').stripped_strings)
            except:
                data = list(soup.select_one('dt:-soup-contains("Lugar principal de ejecución:") + dd').stripped_strings)
            codes = self.format_locations_codes(data)
            return codes

        except AttributeError:
            try:
                data = list(soup.select_one('dt:-soup-contains("Lugar principal de entrega de los suministros:") + dd dl').stripped_strings)
                case1 = True
            except AttributeError:
                try:
                    data = list(soup.select_one('dt:-soup-contains("Lugar principal de entrega de los suministros:") + dd').stripped_strings)
                    case2 = True
                except:
                    return 'es'
            # TEMPORAL return only main code, code commented below returns all codes
            if case1:
                codes = data[1][:-1]
                codes = ''.join(codes)
                return codes.lower()
            elif case2:
                codes = ''.join(data)
                codes = codes[:-1]
                return codes.lower()

            # # Keep only codes in elements with more info
            # for idx, el in enumerate(data):
            #     if "Lote" in el:
            #         el = el.split(": ")[1]
            #         data[idx] = el

            # # Keep only codes from the list
            # codes = [x for x in data if x.startswith("ES")]
            # # Delete duplicate codes and format codes
            # codes = list(dict.fromkeys(codes))
            # codes = self.format_locations_codes(codes)
            # return codes
        except:
            return ""

    def get_bidders_number(self, soup):
        try:
            data = list(soup.select_one('dt:-soup-contains("Número de ofertas recibidas:") + dd').stripped_strings)
            return data[0][:-1]
        except:
            return None

    def format_locations_codes(self, codes):
        try:
            codes = self.delete_element_from_list(".", codes)
            codes = ','.join(codes)
            return codes.lower()
        except:
            return ""

    def get_location(self, locationRepo, tokens):
        locations = asyncio.run(locationRepo.getLocationFromTokens(tokens))
        return locations

    def delete_element_from_list(self, element, deleteList):
        for idx, el in enumerate(deleteList):
            if element in el:
                el = el.replace(element, "")
                deleteList[idx] = el
        return deleteList

    def get_contract_value(self, soup):
        try:
            data = list(soup.select_one('dt:-soup-contains("Valor estimado") + dd').stripped_strings)
        except AttributeError:
            try:
                data = list(soup.select_one('dt:-soup-contains("Valor de la oferta seleccionada") + dd').stripped_strings)
            except:
                return None
        
        value = data[0].split(" ")[0]
        value = self.format_stringNumber(value)
        return value

    def format_stringNumber(self,number):
        formattedNumber = float(number.replace(".", "").replace(",", "."))
        return formattedNumber

    def notify_error(self, errorMessage):
        print(errorMessage)

    def is_valid(self):
        return bool(self.expediente) and bool(self.objeto_del_contrato) # and bool(self.estado_de_la_licitación)

    def store(self):

        if (not self.is_valid()):
            print('tender not valid')
            return

        data = {
            'expedient':                    self.expediente,
            'name':                         self.objeto_del_contrato,
            # 'contractType':                 self.tipo_de_contrato,
            'cpvCodes':                     self.codigo_cpv,
            # 'awardees':                     self.adjudicatarios,
            # 'valueOffers':                   self.valor_ofertas,
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
            # 'budgetNoTaxes':                self.presupuesto_base_de_licitacion_sin_impuestos,
            'contractEstimatedValue':       self.valor_estimado_del_contrato,
            # 'result':                       self.resultado,
            'successBidderOrganization':    self.adjudicatarios,
            'biddersNumber':                self.numero_licitadores,
            # 'awardAmount':                  self.importe_adjudicacion,
            # 'documents':                    self.documents,
            # 'sheets':                       self.sheets,
            'match':                        self.match
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key": os.environ["API_KEY"]
        }

        response = requests.post(
            os.environ["API_URL"]+'/v1/tenders/source/boe/create', headers=headers, json=data)

        print("Status Code", response.status_code)
