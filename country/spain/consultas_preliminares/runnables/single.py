import sys

from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from cp import CP
from runnable import *

# start
print('start...')
start = datetime.now()

url = "https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=8IU%2Fug%2FTre%2FnSoTX3z%2F7wA%3D%3D&isConsPre=1"
licitacion = CP(url, None)

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, 'Contratacion del Estado', 'single')

# end
print('...finished')