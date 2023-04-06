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

from lboe import LBOE
from runnable import *

# start
if os.environ['ENVIRONMENT'] == 'production':
    bugsnag.configure(
        api_key="31adc527bd20e55d8b1a9672f181b2e1",
        project_root=os.path.abspath("runnables"),
    )

print("start...")
start = datetime.now()

# url = "https://www.boe.es/diario_boe/xml.php?id=BOE-B-2022-38680" # has to come as an argument
url = "https://www.boe.es/diario_boe/xml.php?id=BOE-B-2022-38858"
licitacion = LBOE(url, True)

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, "Boletín Oficial del Estado", "single")

# end
print("...finished")