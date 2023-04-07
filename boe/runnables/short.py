############################################################################################################################
# This script checks all tenders published today.
# It will be executed every 1 time each morning at 9AM
############################################################################################################################

import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../.env")

sys.path.append("../src")
sys.path.append("../../utils")

from driver import *
from lboe import LBOE
from runnable import *

# start
print('start...')
counter = 0
start = datetime.now()

# get soup
date = datetime.today().strftime("%Y-%m-%d").replace("-", "")
soup = get_soup_from_url("https://www.boe.es/diario_boe/xml.php?id=BOE-S-" + date, "lxml")

# get seccion
seccion = soup.select('seccion[num*="5A"]')

# check if seccion exists
if(seccion is None):
    sys.exit()

# get departments
departments = seccion[0].findAll('departamento')
for department in departments:
    items = department.findAll('item')
    for item in items:
        url = "https://www.boe.es" + item.urlxml.text
        licitacion = LBOE(url, True)
        counter += 1

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Boletín Oficial del Estado', 'short')

# end
print('...finished')