############################################################################################################################
# This script scrapes all tenders from the file passed as an argument to the script
# To execute, run py scanAtomFile.py path, where path is the path to the file that must get scrapped
############################################################################################################################

import sys
import os
import re
import os.path
import shutil
import tempfile
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../.env")

sys.path.append('./../src')
sys.path.append("../../utils")

from lcde import LCDE
from runnable import *

def format_date(date:str):
    date = date[:-10].replace('-', '').replace('T', '').replace(':', '')
    indx = [0,4,6,8,10,12]
    parts = [date[i:j] for i,j in zip(indx, indx[1:]+[None])]
    return parts[2] + '/' + parts[1] + '/' + parts[0] + ' ' + parts[3] + ':' + parts[4] + ':' + parts[5]

#start
print('start...')
counter = 0
start = datetime.now()

def readFile(path):
    global counter
    file = open(path, encoding='utf-8')

    soup = BeautifulSoup(file, 'lxml')
    items = soup.findAll('entry')

    for idx, item in enumerate(items):

        try:
            status = 'No definido'
            if item.find('cbc-place-ext:contractfolderstatuscode').string == 'RES':
                status = 'Resuelta'

            try:
                contractEstimatedValue = item.find('cbc:estimatedoverallcontractamount').string
            except:
                contractEstimatedValue = None

            try:
                budgetNoTaxes = item.summary.string.split(';')[2].split(': ')[1]
                budgetNoTaxes = re.sub('[^\d\.]', '', budgetNoTaxes)
            except:
                try:
                    budgetNoTaxes = item.summary.string.split(',')[2].split(': ')[1]
                    budgetNoTaxes = re.sub('[^\d\.]', '', budgetNoTaxes)
                except:
                    budgetNoTaxes = item.findAll('cac:budgetamount')[0].find('cbc:taxexclusiveamount').string
                    budgetNoTaxes = re.sub('[^\d\.]', '', budgetNoTaxes)

            try:
                contractingOrganization = item.summary.string.split(';')[1].split(': ')[1]
            except:
                contractingOrganization = item.summary.string.split(',')[1].split(': ')[1]

            try:
                if item.find('cac:tenderresult'):
                    successBidderOrganization = item.find('cac:tenderresult').find('cbc:name').string
                else:
                    successBidderOrganization = None
            except:
                successBidderOrganization = None

            try:
                codes = item.findAll('cbc:itemclassificationcode')
                cpvsList = []
                for code in codes:
                    cpvsList.append(code.string + ".")
                cpvs = ','.join(cpvsList)
            except:
                cpvs = None

            # For some reason numbers with no decimals get last two digits deleted at BE, didn't find why so I add two decimals here
            if "." not in budgetNoTaxes:
                budgetNoTaxes = budgetNoTaxes + ".00"
            if "." not in contractEstimatedValue:
                contractEstimatedValue = contractEstimatedValue + ".00"

            data = {
                    'expedient':                    item.summary.string.split(';')[0].split(': ')[1],
                    'name':                         item.title.string,
                    'contractType':                 'No definido', # didn't find it in the document
                    'status':                       status,
                    'sourceUrl':                    item.link['href'],
                    'linkUrl':                      item.link['href'],
                    'cpvCodes':                     cpvs,
                    'expedientUpdatedAt':           format_date(item.updated.string),
                    'expedientCreatedAt':           format_date(item.updated.string),
                    'procedure':                    'No definido', # didn't find it in the document
                    'contractingOrganization':      contractingOrganization,
                    'budgetNoTaxes':                budgetNoTaxes,
                    'contractEstimatedValue':       contractEstimatedValue,
                    'successBidderOrganization':    successBidderOrganization,
                }

            counter += 1

            headers = {
                    "Content-Type": "application/json; charset=utf-8",
                    "Api-Key" : os.environ["API_KEY"]
                }

            response = requests.post(os.environ["API_URL"]+'/v1/tenders/source/contratacionesdelestado/create', headers=headers, json=data)

            print("Status Code", response.status_code)
        except Exception as ex:
            print(f"For file {path} for entry {item.link['href']}", file=sys.stderr)
            print(ex, file=sys.stderr)

archiveFile = sys.argv[1]

if os.path.isfile(archiveFile):
    if os.access(archiveFile, os.R_OK) and archiveFile.endswith(".zip"):
        print("Attempting decompress file")
        destFolder = tempfile.mkdtemp()
        try:
            shutil.unpack_archive(archiveFile, destFolder)
        except ValueError:
            print("Couldn't extract file")
        archiveFile = destFolder
    else:
        print("Path is a file that doesn't seem a compressed archive")

fileList = os.listdir(archiveFile)
for fileItem in fileList:
    if not fileItem.endswith(".atom"):
        continue

    fullPath = os.path.abspath(os.path.join(archiveFile, fileItem))
    if not os.path.isfile(fullPath):
        continue
    if not os.access(fullPath, os.R_OK):
        print(f"Cannot read file {fileItem}")
        continue

    print(f"Attempting parse file {fileItem}")
    readFile(fullPath)

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Contratacion del Estado', 'scanAtomFolder')

# end
print('...finished')