import re
import threading
import time

from lcde import LCDE

def single_thread(url):
    licitacion = LCDE("https://contrataciondelestado.es" + url, None, True)

def get_items_from_page(soup, counter, tableName):
    table = soup.find('table', id=re.compile(tableName))
    links = table.findAll('a', href=True)
    threads = []
    for link in links:
        t = threading.Thread(target=single_thread, args=(link['href'],))
        t.start()
        time.sleep(1)
        threads.append(t)

    for thread in threads:
        thread.join()

    return counter + len(links)

def get_current_page_number(soup, idText):
    item = soup.find('span', id=re.compile(idText))
    return int(item.get_text()) if item else 0

def get_total_page_number(soup, idText):
    item = soup.find('span', id=re.compile(idText))
    return int(item.get_text()) if item else 0