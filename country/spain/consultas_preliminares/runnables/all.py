import bugsnag
import os
import sys
import re
import time
from datetime import datetime
from lxml import etree
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from runnable import *
from cp import CP

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
driver = get_driver_from_url("https://contrataciondelestado.es/wps/portal/licitaciones")

# Click on "Consultas de mercado"
WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='contenido']/div[4]/a[1]")))
driver.find_element(By.XPATH, "//div[@id='contenido']/div[4]/a[1]").click()

# Click on search button
driver.find_element(By.XPATH, "//div[@id='contenidoBuscador']/fieldset[1]/ul[1]/li[1]/input[1]").click()
time.sleep(0.3)
soup = get_soup_from_driver(driver, "html.parser")

# look for all pages
page = 1
totalPages = int(soup.find('span', id=re.compile('textTotalPagina')).text)
print("Pages: " + str(totalPages))
firstPage = True

IDs = []

while(page <= totalPages):
    print('-' * 30)
    print("Page: " + str(page) + "/" + str(totalPages) )

    WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='contenidoPagina']/form[1]/table[1]")))
    soup = get_soup_from_driver(driver, "html.parser")

    # Get number of elements in table
    table = soup.find('table', id=re.compile('tablaResultadosConsultas'))
    elements = table.tbody.findChildren('tr', recursive=False)

    soup = get_soup_from_driver(driver, "html.parser")
    dom = etree.HTML(str(soup))

    # save all ids in table
    visitedElements = 0
    while(visitedElements < len(elements)):
        elementNumber = visitedElements + 1
        elementPath = "//div[@id='contenidoPagina']/form[1]/table[1]/tbody[1]/tr[" + str(elementNumber) + "]/td[1]/a[1]/span[1]"

        IDs.append(dom.xpath(elementPath)[0].text)
        visitedElements +=1
        

    if(page != totalPages):
        # navigate to new page
        if firstPage:
            nextBtnXpath = "//div[@id='contenidoPagina']/form[1]/table[1]/tfoot[1]/tr[1]/td[1]/input[1]"
            firstPage = False
        else:
            nextBtnXpath = "//div[@id='contenidoPagina']/form[1]/table[1]/tfoot[1]/tr[1]/td[1]/input[3]"
        element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, nextBtnXpath)))
        element = driver.find_element("xpath", nextBtnXpath).click()
        soup = get_soup_from_driver(driver, "html.parser")
    
    page += 1

print('\nTotal elements to search: ' + str(len(IDs)))

# search every single element and save it
exitBtnPath = "//div[@id='mainContent']/div[1]/div[1]/div[1]/div[1]/fieldset[1]/form[1]/div[1]/input[1]"
searchedElements = 1
while(searchedElements <= len(IDs)):
    try:
        print('Element ' + str(searchedElements) + '/' + str(len(IDs)) + ': ' + IDs[searchedElements - 1])
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='contenidoBuscador']/div[1]/ul[1]/li[2]/input[1]")))
        inputElement = driver.find_element(By.XPATH, "//div[@id='contenidoBuscador']/div[1]/ul[1]/li[2]/input[1]")
        inputElement.clear()
        inputElement.send_keys(IDs[searchedElements - 1])
        inputElement.send_keys(Keys.ENTER)

        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='contenidoPagina']/form[1]/table[1]")))
        soup = get_soup_from_driver(driver, "html.parser")
        
        # Get number of elements in table
        table = soup.find('table', id=re.compile('tablaResultadosConsultas'))
        elements = table.tbody.findChildren('tr', recursive=False)

        if len(elements) > 1:
            found = False
            firstPage = True
            while not found:
                position = 1
                for element in elements:
                    span = element.select_one('span[class*=outputText]')
                    if span.text == IDs[searchedElements - 1]:
                        found = True
                        break
                    position += 1

                if found:
                    break

                # navigate to new page
                if firstPage:
                    nextBtnXpath = "//div[@id='contenidoPagina']/form[1]/table[1]/tfoot[1]/tr[1]/td[1]/input[1]"
                    firstPage = False
                else:
                    nextBtnXpath = "//div[@id='contenidoPagina']/form[1]/table[1]/tfoot[1]/tr[1]/td[1]/input[3]"
                element = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, nextBtnXpath)))
                element = driver.find_element("xpath", nextBtnXpath).click()
                soup = get_soup_from_driver(driver, "html.parser")

            try:
                elementPath = "//div[@id='contenidoPagina']/form[1]/table[1]/tbody[1]/tr[" + str(position) + "]/td[1]/a[1]"
                driver.find_element(By.XPATH, elementPath).click()

                # get data
                soup = get_soup_from_driver(driver, "html.parser")
                CP(driver.current_url, soup)

                WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, exitBtnPath)))
                driver.find_element(By.XPATH, exitBtnPath).click()
            
            except Exception as e:
                print("Error finding element " + IDs[searchedElements - 1])
                print("Error: " + str(e))

        else:
            driver.find_element(By.XPATH, "//div[@id='contenidoPagina']/form[1]/table[1]/tbody[1]/tr[1]/td[1]/a[1]").click()

            # get data
            soup = get_soup_from_driver(driver, "html.parser")
            CP(driver.current_url, soup)

            WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, exitBtnPath)))
            driver.find_element(By.XPATH, exitBtnPath).click()

    except:
        print("Error")
        # Click on "Consultas de mercado"
        driver.get("https://contrataciondelestado.es/wps/portal/licitaciones")
        WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='contenido']/div[4]/a[1]")))
        driver.find_element(By.XPATH, "//div[@id='contenido']/div[4]/a[1]").click()

    searchedElements += 1

# kill driver
driver.quit()

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Consultas Preliminares', 'all')

# end
print('...finished')