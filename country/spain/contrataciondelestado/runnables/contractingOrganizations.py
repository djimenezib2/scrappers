############################################################################################################################
# This script checks all the pages from the contracting Organizations list
############################################################################################################################

import sys
import time
import bugsnag
import os
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from lib import *
from runnable import *
from ccde import CCDE

# start
if os.environ['ENVIRONMENT'] == 'production':
    bugsnag.configure(
        api_key="31adc527bd20e55d8b1a9672f181b2e1",
        project_root=os.path.abspath("runnables"),
    )

print('start...')
counter = 0
start = datetime.now()

# get driver
driver = get_driver_from_url("https://contrataciondelestado.es/wps/portal/perfilContratante")

# change filter to all organizations
WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'comboactivo')]")))
driver.find_element(By.XPATH, "//select[contains(@id, 'comboactivo')]").click()
driver.find_element(By.XPATH, "//select[contains(@id, 'comboactivo')]/option[@value=0]").click()

#Click on search button
driver.find_element(By.XPATH, "//input[contains(@id, 'botonbuscar')]").click()

# look for all pages
WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH, "//span[contains(@id, 'textTotalPagina')]")))
soup = get_soup_from_driver(driver, "html.parser")

currentPage = 1
totalPages = get_total_page_number(soup, "textTotalPagina")
print("Total pages: " + str(totalPages))
print("-" * 30)
while(currentPage < totalPages):
    print("Page " + str(currentPage) + "/" + str(totalPages))
    print("-" * 30)
    # Get number of elements in table
    WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH, "//table[contains(@id, 'tableBusquedaPerfilContratante')]")))
    elements = len(soup.select('#tableBusquedaPerfilContratante > tbody tr'))
    
    # Get into every element, get soup and generate Contracting Organization
    visitedElements = 0
    while(visitedElements < elements):
        print(str(visitedElements + 1) + "/" + str(elements))
        elementNumber = visitedElements + 1
        elementPath = "//table[@id='tableBusquedaPerfilContratante']/tbody/tr[" + str(elementNumber) + "]/td[1]/a"

        try:
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, elementPath)))
            driver.find_element(By.XPATH, elementPath).click()
            time.sleep(0.5)
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//form[contains(@id, 'perfilComp')]")))
            soup = get_soup_from_driver(driver, "html.parser")
            CCDE(soup)
            counter += 1

            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'idBotonVolver')]")))
            driver.find_element(By.XPATH, "//input[contains(@id, 'idBotonVolver')]").click()
            time.sleep(0.5)
            visitedElements += 1

        except Exception as e:
            try:
                print("Page crashed and restarted, navigating to last page I visited")
                
                # Page reset, we apply filters again and navigate to last page
                # change filter to all organizations
                WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'comboactivo')]")))
                driver.find_element(By.XPATH, "//select[contains(@id, 'comboactivo')]").click()
                driver.find_element(By.XPATH, "//select[contains(@id, 'comboactivo')]/option[text()='-- Todos --']").click()

                #Click on search button
                driver.find_element(By.XPATH, "//input[contains(@id, 'botonbuscar')]").click()

                # navigate to last page where crashed
                page = 1
                while(page < currentPage):
                    print(str(page) +"/"+str(currentPage))
                    WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'siguienteLink')]")))
                    driver.find_element(By.XPATH, "//input[contains(@id, 'siguienteLink')]").click()
                    page += 1
                    time.sleep(0.5)

            except:
                print("Page crashed and restarted, navigating to last page I visited")


    # navigate to new page unless it's last page
    if(currentPage != totalPages):
        WebDriverWait(driver,60).until(EC.presence_of_element_located((By.XPATH, "//input[contains(@id, 'siguienteLink')]")))
        driver.find_element(By.XPATH, "//input[contains(@id, 'siguienteLink')]").click()
        time.sleep(0.5)

    # update soup
    soup = get_soup_from_driver(driver, "html.parser")

    # update current page
    currentPage = get_current_page_number(soup, 'textNumPag')

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Contratacion del Estado', 'organizations')

# end
print('...finished')