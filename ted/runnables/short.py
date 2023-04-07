import sys
import re
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from dotenv import load_dotenv

load_dotenv("../../.env")

sys.path.append("../src")
sys.path.append("../../utils")

from driver import *
from lted import LTED
from runnable import *

# start
print('start...')
counter = 0
start = datetime.now()

# get soup
driver = get_driver_from_url("https://ted.europa.eu/TED/browse/browseByMap.do")
actions = ActionChains(driver)

# change language to spanish
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "lgId")))
driver.find_element(By.ID, "lgId").click()
driver.find_element(By.XPATH, "//select[@id='lgId']/option[text()='español (es)']").click()

# click on "Busqueda avanzada"
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "goToSearch")))
driver.find_element(By.ID, "goToSearch").click()

# accept cookies and close tab
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "cookie-consent-banner")))
driver.find_element(By.XPATH, "//div[@id='cookie-consent-banner']/div[1]/div[1]/div[2]/a[1]").click()
driver.find_element(By.XPATH, "//div[@id='cookie-consent-banner']/div[1]/div[1]/div[2]/button[1]").click()

# click on specific date and set to today
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "publicationDateSpecific")))
element = driver.find_element(By.ID, "publicationDateSpecific")
element.send_keys(datetime.now().strftime("%d/%m/%Y"))

# click on search
driver.find_element(By.ID, "search").click()

# go trough all pages and create all tenders
nextPage = True

while nextPage:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "notice")))

    # create tenders
    # TODO Revisar selenium.common.exceptions.WebDriverException: Message: unknown error: session deleted because of page crash from tab crashed
    soup = get_soup_from_driver(driver, "html.parser")

    items = soup.find("table", {"id": "notice"})
    for a in items.findAll("a", href=True):
        if not "searchResult" in a["href"]:
            url = "https://ted.europa.eu" + a["href"]
            try:
                pageSoup = get_soup_from_url(url, "html.parser")
                isTest = bool(pageSoup.find_all(text = re.compile("\[TEST"))) or bool(pageSoup.find_all(text = re.compile("\[Test"))) or bool(pageSoup.find_all(text = re.compile("Lorem ipsum"))) or bool(pageSoup.find_all(text = re.compile("Ut iusto")))
                if not isTest:
                    licitacion = LTED(url, pageSoup, True)
            except Exception as ex:
                print("Error")

    # if text appears with href we can go to next page
    if bool(driver.find_elements(By.XPATH, "//span[@class='pagelinks']//a[@href][contains(.,'Sig')]")):
        driver.find_element(By.XPATH, "//span[@class='pagelinks']/a[text()='Sig']").click()

    #if text appears without href we already are at last page
    else:
        nextPage = False

# manage runnable
end = datetime.now()
store_runnable(start, end, counter, 'Contrataciones Menores', 'short')

# end
print('...finished')