############################################################################################################################
# This script checks only one tender.
# It will be executed triggered by the admin user. No chron execution.
############################################################################################################################

import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from ldre import LDRE
from runnable import *

# start
print('start...')
start = datetime.now()

url = "https://dre.pt/dre/detalhe/anuncio-procedimento/2225-2023-207485780"  # this will come as an argument   
licitacion = LDRE(url, None, True)

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, 'Diário da República Electrónico', 'single')

# end
print('...finished')