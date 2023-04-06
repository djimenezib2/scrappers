############################################################################################################################
# This script checks all the pages from the tenders list. Data from 14 years. Aprox ~750k tenders.
# It will be executed every month. It takes 10 days to be fully executed.
############################################################################################################################

import sys
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from lib import *
from runnable import *

def single_driver(i):

    global counter

    # go to main tender site
    print('go to main tender site...')
    driver = get_driver_from_url("https://contrataciondelestado.es/wps/portal/licitaciones")
    soup = get_soup_from_driver(driver, "html.parser")

    # click "Licitaciones"
    print('click on licitaciones...')
    element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".requestLink")))
    element = driver.find_element(By.XPATH, "//a[contains(@id,'linkFormularioBusqueda')]")
    element.click()

    # click buscar (and wait) and update soup
    print('click buscar (and wait) and update soup...')
    element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".commandExButton")))
    element = driver.find_element(By.XPATH, "//input[contains(@id,'button1')]")
    element.click()
    element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".botonEnlace")))
    soup = get_soup_from_driver(driver, "html.parser")

    # look for all pages
    j = 1
    total = get_total_page_number(soup, "textfooterInfoTotalPaginaMAQ")
    print("Pages: " + str(total))
    while(j <= total):

        # update current page counter
        current_page = get_current_page_number(soup, "textfooterInfoNumPagMAQ")

        # read content
        tenders = soup.select('td[class*="tdExpediente"]')

        # navigate to tender    
        element = driver.find_element("xpath", "//a[contains(@id,'enlaceExpediente_"+str(i)+"')]")
        element.click()

        # get soup
        soup = get_soup_from_driver(driver, "html.parser")

        # create tender
        licitacion = LCDE(None, soup, False)
        counter += 1
        print(counter)

        # navigate back
        element = driver.find_element("xpath", "//a[contains(@id,'enlace_volver')]")
        element.click()

        # navigate to new page
        element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".botonEnlace")))
        element = driver.find_element("xpath", "//input[contains(@id,'footerSiguiente')]")
        element.click()

        # update soup
        soup = get_soup_from_driver(driver, "html.parser")

        # update counter
        j += 1

    # kill drivers
    driver.quit()

# start
print('start...')
counter = 0
start = datetime.now()

drivers = []
for i in range(20):
    t = threading.Thread(name='Thread driver {}'.format(i), target=single_driver, args=(i,))
    t.start()
    time.sleep(1)
    print(t.name + ' started!')
    drivers.append(t)

# Wait for all of them to finish
for driver in drivers:
    driver.join()

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Contratacion del Estado', 'long')

# end
print('...finished')