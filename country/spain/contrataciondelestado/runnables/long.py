############################################################################################################################
# This script checks all the pages from the latest tenders.
# It will be executed every 3 hours (8 times a day).
############################################################################################################################

import sys
import bugsnag
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from lib import *
from runnable import *

# start
if os.environ['ENVIRONMENT'] == 'production':
    bugsnag.configure(
        api_key="31adc527bd20e55d8b1a9672f181b2e1",
        project_root=os.path.abspath("runnables"),
    )

print('start...')
counter = 0
start = datetime.now()

# get lasts (most recent)
driver = get_driver_from_url("https://contrataciondelestado.es/wps/portal/licRecientes")
soup = get_soup_from_driver(driver, "html.parser")

# look for all pages
i = 1
total = get_total_page_number(soup, "liciRecientes:textTotalPagina")
print("Pages: " + str(total))
while(i <= total):

    # update current page counter
    current_page = get_current_page_number(soup, "liciRecientes:textNumPag")

    # read content
    counter = get_items_from_page(soup, counter, "tabla_liciRecientes")

    print('-' * 30)
    print("Page: " + str(current_page) + "/" + str(total) )
    print("Licitaciones: " + str(counter))
    print('-' * 30)

    if(i != total):
        # navigate to new page
        element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".botonEnlace")))
        element = driver.find_element("xpath", "//input[contains(@id,'liciRecientes:siguienteLink')]")
        element.click()

        # update soup
        soup = get_soup_from_driver(driver, "html.parser")

    # update counter
    i = i + 1

# kill driver
driver.quit()

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Contratacion del Estado', 'long')

# end
print('...finished')