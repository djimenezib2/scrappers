import sys
import time
import traceback
import atexit
from datetime import datetime
from selenium import webdriver      # Selenium is a web testing library. It is used to automate browser activities.
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup       # Beautiful Soup is a Python package for parsing HTML and XML documents. It creates parse trees that is helpful to extract the data easily.

drivers = []
def driver_cleaner():
    global drivers
    [driver.quit() for driver in drivers]
    drivers = []

atexit.register(driver_cleaner)

last_navigation = datetime.now()
navigation_wait = 2

min_fail_wait = 10
max_fail_wait = 60 * 30
backoff_growth_fail_wait = 2

def get_driver_from_url(url):
    global last_navigation
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox") 
    options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless") 
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option("useAutomationExtension", False);
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    drivers.append(driver)

    nav_dif = (datetime.now() - last_navigation).total_seconds()
    if nav_dif < navigation_wait :
        time.sleep(navigation_wait - nav_dif)
    last_navigation = datetime.now()
    
    isDriverNavigated = False
    openAttempts = 0
    while not isDriverNavigated and openAttempts < 10:
        try:
            driver.get(url)
            isDriverNavigated = True
        except Exception as e:
            print("Failed open attempt")
            if openAttempts == 0:
                print(e)
            openAttempts += 1
            time.sleep(min_fail_wait + min(pow(backoff_growth_fail_wait, openAttempts), max_fail_wait))
    
    if not isDriverNavigated:
        raise Exception(f"Cannot open {url} after {openAttempts} attempts")

    return driver

def get_soup_from_url(url, parser):
    driver = get_driver_from_url(url)
    content = driver.page_source
    soup = BeautifulSoup(content, parser)
    driver.quit()
    return soup

def get_soup_from_driver(driver, parser):
    content = driver.page_source
    soup = BeautifulSoup(content, parser)
    return soup

def get_page_source_from_url(url):
    driver = get_driver_from_url(url)
    driver.quit()
    return driver.page_source

def get_soup_dynamic_webpage(url, ecx=None, clickFirst=None):
    try:
        driver = get_driver_from_url(url)

        # if something needs to be confirmed by click
        if clickFirst:
            WebDriverWait(driver, 25).until(EC.visibility_of_all_elements_located((By.XPATH, clickFirst)))
            driver.find_element(By.XPATH, clickFirst).click()

        # if some section needs to be loaded first
        if ecx:
            WebDriverWait(driver, 25).until(EC.visibility_of_all_elements_located((By.XPATH, ecx)))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()
        return soup
    except Exception as e:
        print(e)
        return None