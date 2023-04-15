############################################################################################################################
# This script checks all pages from the latest tenders.
############################################################################################################################

import sys
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv("../../.env")

sys.path.append("../src")
sys.path.append("../../utils")

from driver import *
from lcm import LCM
from runnable import *
from functions import *

# start
print('start...')
counter = 0
start = datetime.now()

# get soup
driver = get_driver_from_url("https://contrataciondelestado.es/wps/portal/licitaciones")
time.sleep(0.5)

# Click on "Contratos Menores"
WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='contenido']/div[2]/a[1]")))
driver.find_element(By.XPATH, "//div[@id='contenido']/div[2]/a[1]").click()
time.sleep(0.3)

# Set Search Criterias
WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.ID, "contenidoBuscador")))
driver.find_element(By.XPATH, "//div[@id='contenidoBuscador']/div[1]/ul[5]/li[2]/select[1]").click()
driver.find_element(By.XPATH, "//div[@id='contenidoBuscador']/div[1]/ul[5]/li[2]/select[1]/option[text()='Publicada']").click()
driver.find_element(By.XPATH, "//div[@id='contenidoBuscador']/div[1]/ul[5]/li[4]/input[1]").clear()

# Click on search button
driver.find_element(By.XPATH, "//div[@id='contenidoBuscador']/fieldset[1]/ul[1]/li[1]/input[1]").click()
time.sleep(0.3)
soup = get_soup_from_driver(driver, "html.parser")

# look for all pages
page = 1
total = get_total_page_number(soup, "textfooterInfoTotalPaginaMAQ")
print("Pages: " + str(total))

while(page <= total):
    
    currentPage = get_current_page_number(soup, "textfooterInfoNumPagMAQ")
    print("\nPage " + str(currentPage) + "/" + str(total))

    # Get number of elements in table
    elements = len(soup.select('#myTablaBusquedaCustom > tbody tr'))

    # Get into every element, get soup, generate tender
    visitedElements = 0
    while(visitedElements < elements):
        elementNumber = visitedElements + 1
        elementPath = "//table[@id='myTablaBusquedaCustom']/tbody/tr[" + str(elementNumber) + "]/td[1]/div[1]/a"
        
        driver.find_element(By.XPATH, elementPath).click()
        time.sleep(0.5)
        soup = get_soup_from_driver(driver, "html.parser")
        licitacion = LCM(driver.current_url, soup, True)
        counter += 1

        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.ID, "enlace_volver")))
        driver.find_element(By.ID, "enlace_volver").click()
        time.sleep(0.5)
        visitedElements += 1

    if(page != total):
        # navigate to new page
        element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".botonEnlace")))
        element = driver.find_element("xpath", "//input[contains(@id,'footerSiguiente')]")
        element.click()

        # update soup
        soup = get_soup_from_driver(driver, "html.parser")

    page = page + 1

# manage runnable
driver.quit()
end = datetime.now()
store_runnable(start, end, counter, 'Contrataciones Menores', 'short')

# end
print('...finished')