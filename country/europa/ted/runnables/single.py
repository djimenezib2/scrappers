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

from lted import LTED
from runnable import *

# start
print("start...")
start = datetime.now()

# Formato con varios códigos NUTS, de momento funciona porqué solo se usa el nuts del país, no el específico
# url = "https://ted.europa.eu/udl?uri=TED:NOTICE:696761-2022:TEXT:ES:HTML&src=0"

url = "https://ted.europa.eu/udl?uri=TED:NOTICE:82255-2023:TEXT:ES:HTML"
licitacion = LTED(url, None, True)

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, "Tenders Electronic Daily", "single")

# end
print("...finished")