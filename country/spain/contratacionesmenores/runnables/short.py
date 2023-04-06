############################################################################################################################
# This script checks only the first page from the latest tenders.
# It will be executed every 1 minute, 60 times per hour, 1.440 times per day.
############################################################################################################################

import sys
import time
import bugsnag
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from lcm import LCM
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

# manage runnable
driver.quit()
end = datetime.now()
store_runnable(start, end, counter, 'Contrataciones Menores', 'short')

# end
print('...finished')