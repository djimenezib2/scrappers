############################################################################################################################
# This script checks all tenders from 5 years from now.
# It will be executed once in production
############################################################################################################################

import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from lboe import LBOE
from runnable import *

def dateToString(date):
    stringDate = date.strftime("%Y-%m-%d").replace("-", "")
    return stringDate

# start
print("start...")
counter = 0
start = datetime.now()

# get soup

startDate = datetime.today()
endDate = datetime.today() - timedelta(days = 1825) # 5 years



while startDate > endDate:
    # Change url for next one
    url = "https://www.boe.es/diario_boe/xml.php?id=BOE-S-" + dateToString(startDate)
    
    # Get soup
    soup = get_soup_from_url(url, "lxml")

    # Get section
    section = soup.select('seccion[num*="5A"]')

    # Check if section exists
    if(section is None):
        sys.exit()

    # get departments
    print("")
    print(url)
    print("")

    # In case BOE page returns "No se encontró el sumario original" we skip to the next page
    try:
        departments = section[0].findAll("departamento")
        for department in departments:
            items = department.findAll("item")
            for item in items:
                url = "https://www.boe.es" + item.urlxml.text
                licitacion = LBOE(url, False)
                counter += 1

        # Change startDate for nexr date
        startDate -= timedelta(days = 1)
    
    except IndexError:
        startDate -= timedelta(days = 1)

# Manage runnable
end = datetime.now()
store_runnable(start, end, counter, "Boletín Oficial del Estado", "all")

# end
print("...finished")