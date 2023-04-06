############################################################################################################################
# This script checks only the first page from the latest tenders.
# It will be executed every 1 minute, 60 times per hour, 1.440 times per day.
############################################################################################################################

import sys
import bugsnag
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from urllib.request import Request, urlopen

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from lgct import LGCT
from runnable import *

def get_json(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urlopen(req).read()
    data = json.loads(response)
    return data

# start
if os.environ['ENVIRONMENT'] == 'production':
    bugsnag.configure(
        api_key="31adc527bd20e55d8b1a9672f181b2e1",
        project_root=os.path.abspath("runnables"),
    )

print('start...')
counter = 0
start = datetime.now()

# get json
url = "https://contractaciopublica.cat/portal-api/ultimes-publicacions?page=0&size=20&tipus=104"
data = get_json(url)
for item in data['content']:
    itemUrl = 'https://contractaciopublica.cat/portal-api/detall-publicacio-expedient/' + str(item['id'])
    itemData = get_json(itemUrl)
    try:
        tender = LGCT(itemData, itemUrl, item['urlPublicacio'], True)
        counter += 1
    except:
       pass 



# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Gencat', 'short')

# end
print('...finished')
