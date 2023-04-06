import sys
import json
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

print('start...')

url = 'https://contrataciondelestado.es/wps/poc?uri=deeplink%3Adetalle_licitacion&idEvl=aWUWH%2BuhW1aXQV0WE7lYPw%3D%3D'
data = get_json(url)
tender = LGCT(data, url, url, False)

# end
print('...finished')
