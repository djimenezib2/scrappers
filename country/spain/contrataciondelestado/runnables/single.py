############################################################################################################################
# This script checks only one tender.
# It will be executed triggered by the admin user. No chron execution.
############################################################################################################################

import sys
import bugsnag
import os

from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from lcde import LCDE
from runnable import *

# start
if os.environ['ENVIRONMENT'] == 'production':
    bugsnag.configure(
        api_key="31adc527bd20e55d8b1a9672f181b2e1",
        project_root=os.path.abspath("runnables"),
    )

print('start...')
start = datetime.now()

url = "https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=LZ9pQcGuMm8uf4aBO%2BvQlQ%3D%3D"
licitacion = LCDE(url, None, True)

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, 'Contratacion del Estado', 'single')

# end
print('...finished')