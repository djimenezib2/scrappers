############################################################################################################################
# This script checks only the first page from the latest tenders.
# It will be executed every 1 minute, 60 times per hour, 1.440 times per day.
############################################################################################################################

import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from lcde import LCDE
from runnable import *

# start
print('start...')
counter = 0
start = datetime.now()

# get soup
soup = get_soup_from_url("https://contrataciondelestado.es/wps/portal/licRecientes", "html.parser")

items = soup.find('table', 'licitacionesRecientes')
for a in items.findAll('a', href=True):
    try:
        licitacion = LCDE("https://contrataciondelestado.es" + a['href'], None, True)
        counter += 1
    except:
        print(f"Element {a['href']} skipped")

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Contratacion del Estado', 'short')

# end
print('...finished')
