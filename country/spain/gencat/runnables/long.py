import bugsnag
import sys
import os
import json
from dotenv import load_dotenv
from datetime import datetime
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

lastPage = False
page = 0

while not lastPage:
    url = "https://contractaciopublica.cat/portal-api/ultimes-publicacions?page=" + str(page) + "&size=20&tipus=104"
    data = get_json(url)
    print("Page " + str(page) + " of " + str(data['totalPages']))
    for item in data['content']:
        itemUrl = 'https://contractaciopublica.cat/portal-api/detall-publicacio-expedient/' + str(item['id'])
        itemData = get_json(itemUrl)
        try:
            tender = LGCT(itemData, itemUrl, item['urlPublicacio'], True)
            counter += 1
        except:
            print("Skipping one")
            pass
    if data['last'] == True:
        lastPage = True
    page += 1

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Gencat', 'long')

# end
print('...finished')