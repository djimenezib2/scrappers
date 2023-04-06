import sys
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from dotenv import load_dotenv

load_dotenv("../../../../.env")

sys.path.append("../src")
sys.path.append("../../../../utils")

from driver import *
from ldre import LDRE
from runnable import *

# start
print('start...')
start = datetime.now()

# Get soup
driver = get_driver_from_url("https://www.dre.pt/dre/home")
time.sleep(0.5)

# Click on "Serie II"
WebDriverWait(driver,25).until(EC.presence_of_element_located((By.ID, "b4-Column2")))
driver.find_element(By.ID, "b4-Column2").click()
time.sleep(0.1)

# Click on title
WebDriverWait(driver,25).until(EC.presence_of_element_located((By.CLASS_NAME, "titulo")))
driver.find_element(By.CLASS_NAME, "titulo").click()

# Apply filter L - Contratos Publicos
time.sleep(1)
WebDriverWait(driver,25).until(EC.presence_of_element_located((By.ID, "Dropdown1")))
driver.find_element(By.ID, "Dropdown1").click()
driver.find_element(By.XPATH, "//select[@id='Dropdown1']/option[text()='L - Contratos públicos']").click()

#Click on filter button
driver.find_element(By.XPATH, "//div[@id='Conteudo']/div[3]/div/button").click()
time.sleep(0.5)
soup = get_soup_from_driver(driver, "html.parser")

# Get number of pages
currentPage = 1
try:
    WebDriverWait(driver,3).until(EC.presence_of_element_located((By.ID, "b10-b3-PaginationList")))
    pages = int(driver.find_element(By.XPATH, "//div[@id='b10-b3-PaginationList']/button[last()]/span").get_attribute("innerHTML"))

except (StaleElementReferenceException, NoSuchElementException):
    pages = 1

# Create all tenders on current page
while(currentPage <= pages):

    print('-' * 30)
    print("Page: " + str(currentPage) + "/" + str(pages))

    # Create tenders
    WebDriverWait(driver,25).until(EC.presence_of_element_located((By.ID, "b10-b3-PaginationContainer")))
    items = soup.find("div", {"id": "ListaDiplomaBlock"})
    for a in items.findAll("a", href=True):
        url = "https://www.dre.pt"+a["href"]

        # De momento solo coge licitaciones nuevas, avisos de prorrogacion de plazos y declaraciones de rectificaciones de anuncios lo dejo para la parte de update
        if("aviso-prorrogacao-prazo" not in url):
            licitacion = LDRE(url, None, True)

    # Move to next page if not on last page
    if(currentPage != pages):
        WebDriverWait(driver,25).until(EC.presence_of_element_located((By.XPATH, "//div[@id='b10-b3-PaginationContainer']/button[2]")))
        driver.find_element(By.XPATH, "//div[@id='b10-b3-PaginationContainer']/button[2]").click()

        soup = get_soup_from_driver(driver, "html.parser")

    currentPage += 1

driver.quit()

# manage runnable
end = datetime.now()
store_runnable(start, end, 1, 'Diário da República Electrónico', 'short')

# end
print('...finished')