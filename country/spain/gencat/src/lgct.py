import sys
import asyncio
import os
import requests

sys.path.append("../../../../utils")
sys.path.append("../../../../")

from tokenizer import *
from location_db import *

# Licitacion GENCAT
class LGCT:
    def __init__(self, data, url_fuente, url_enlace, match):

        self.locationRepository = JSONLocationRepository("../../../../location.json")
        
        #...
        self.url_fuente                                         = url_fuente
        self.enlace                                             = url_enlace
        self.expediente                                         = data['codiExpedient']
        # self.ubicacion_organica                                 = "" # que es?
        self.organo_de_contratacion                             = data['dades']['organ']['nom']
        self.estado_de_la_licitación                            = data['dades']['publicacio']['fase']['text']
        self.objeto_del_contrato                                = data["titol"]
        self.presupuesto_base_de_licitacion_sin_impuestos       = data['dades']['publicacio']['dadesPublicacioLot'][0]['pressupostLicitacio']
        self.valor_estimado_del_contrato                        = data['dades']['publicacio']['dadesPublicacioLot'][0]['valorEstimat']
        self.tipo_de_contrato                                   = data['dades']['publicacio']['dadesBasiquesPublicacio']['tipusContracte']['text']
        self.codigo_cpv                                         = self.get_cpv_codes(data)
        self.lugar_de_ejecucion                                 = data['dades']['publicacio']['dadesPublicacioLot'][0]['llocExecucio']['codiNuts']
        self.lugar                                              = self.get_locationNuts(self.locationRepository, tokenize(self.lugar_de_ejecucion))
        self.procedimiento_de_contratacion                      = data['dades']['publicacio']['dadesBasiquesPublicacio']['procedimentAdjudicacio']['text']
        self.fecha_fin_de_presentación_de_oferta                = self.format_date(data['dades']['publicacio']['dadesPublicacio']['dataTerminiPresentacioOSolicitud'])
        self.fecha_de_publicacion_del_expediente                = self.format_date(data['dades']['dataPublicacioReal'])
        self.fecha_de_actualizacion_del_expediente              = self.fecha_de_publicacion_del_expediente
        # self.resultado                                          = ""
        try:
            self.adjudicatario                                  = data['dades']['publicacio']['dadesPublicacioLot'][0]['empresesAdjudicataries'][0] # pueden haber varias entiendo, revisar
        except:
            self.adjudicatario                                  = None
        # self.numero_licitadores                                 = ""
        try:
            self.importe_adjudicacion                           = data['dades']['publicacio']['dadesPublicacioLot'][0]['importAdjudicacio']
        except:
            self.importe_adjudicacion                           = None
        self.documents                                          = ""
        self.sheets                                             = self.get_sheets(data)
        self.match                                              = match
        #...
        self.store()

    def get_locationNuts(self, locationRepo, tokens):
        locations = asyncio.run(locationRepo.getLocationFromTokens(tokens))
        return locations
    
    def get_cpv_codes(self, data):
        codes = []
        for code in data['dades']['publicacio']['dadesPublicacioLot'][0]['codisCpv']:
            codes.append(code['codi'][:-2])
        return ','.join(codes)
    
    def get_successful_bidders(self, data):
        bidders = []
        for bidder in data['dades']['publicacio']['dadesPublicacioLot'][0]['empresesAdjudicataries'][0]:
            bidders.append(bidder['denominacio'])
        return ','.join(bidders)
    
    def format_date(self, date):
        dateHour = date.replace('Z', '').split('T')
        dateParts = dateHour[0].split('-')
        hour = dateHour[1]

        return dateParts[2] + '/' + dateParts[1] + '/' + dateParts[0] + ' ' + hour

    def get_sheets(self, data):
        sheets = []
        for el in data['dades']['publicacio']['dadesPublicacio']['plecsDeClausulesAdministratives']['docs']:
            sheet = {
                'name': el['titol'],
                'url': el['path']
            }
            sheets.append(sheet)

        for el in data['dades']['publicacio']['dadesPublicacio']['plecsDePrescripcionsTecniques']['docs']:
            sheet = {
                'name': el['titol'],
                'url': el['path']
            }
            sheets.append(sheet)

        for el in data['dades']['publicacio']['dadesPublicacio']['memoriaJustificativaContracte']['docs']:
            sheet = {
                'name': el['titol'],
                'url': el['path']
            }
            sheets.append(sheet)

        for el in data['dades']['publicacio']['dadesPublicacio']['documentsAprovacio']['docs']:
            sheet = {
                'name': el['titol'],
                'url': el['path']
            }
            sheets.append(sheet)
        
        for el in data['dades']['publicacio']['dadesPublicacio']['altresDocuments']['docs']:
            sheet = {
                'name': el['titol'],
                'url': el['path']
            }
            sheets.append(sheet)
        
        return sheets

    
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
            'submissionDeadlineDate':       self.fecha_fin_de_presentación_de_oferta,
            'expedientCreatedAt':           self.fecha_de_publicacion_del_expediente,
            'expedientUpdatedAt':           self.fecha_de_actualizacion_del_expediente,
            'procedure':                    self.procedimiento_de_contratacion,
            'contractingOrganization':      self.organo_de_contratacion,
            'budgetNoTaxes':                self.presupuesto_base_de_licitacion_sin_impuestos,
            'contractEstimatedValue':       self.valor_estimado_del_contrato,
            # 'result':                       self.resultado,
            'successBidderOrganization':    self.adjudicatario,
            # 'biddersNumber':                self.numero_licitadores,
            'awardAmount':                  self.importe_adjudicacion,
            # 'documents':                    self.documents,
            'sheets':                       self.sheets,
            'match':                        self.match
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Api-Key" : os.environ["TENDIOS_API_KEY"]
        }

        response = requests.post(os.environ["TENDIOS_API_URL"]+'/v1/tenders/source/gencat/create', headers=headers, json=data)

        print("Status Code", response.status_code)