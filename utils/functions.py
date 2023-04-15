import zlib
import os
import re

from pathlib import Path

def normalize_string(string):
    lower_string = string.lower()
    no_punc_string = re.sub(r'[^\w\s]','_', lower_string)
    no_wspace_string = no_punc_string.replace(' ', '_')
    return no_wspace_string

def get_current_page_number(soup, idText):
    item = soup.find('span', id=re.compile(idText))
    return int(item.get_text()) if item else 0

def get_total_page_number(soup, idText):
    item = soup.find('span', id=re.compile(idText))
    return int(item.get_text()) if item else 0