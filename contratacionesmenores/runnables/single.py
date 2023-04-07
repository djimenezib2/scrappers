############################################################################################################################
# This script checks only one tender.
# It will be executed triggered by the admin user. No chron execution.
############################################################################################################################

import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../.env")

sys.path.append("../src")
sys.path.append("../../utils")

from lcm import LCM
from runnable import *

# start
print('start...')
start = datetime.now()

# Acceder a la url directamente da error ya que no carga la pagina, aparece un cuadro de texto con un error, hay que mirar como acceder por url
url = "https://contrataciondelestado.es/wps/poc?uri=deeplink:detalle_licitacion&idEvl=YwbLEq%2BR1HlvYnTkQN0%2FZA%3D%3D"  # this will come as an argument   
licitacion = LCM(url, None, True)

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, 'Contrataciones Menores', 'single')

# end
print('...finished')