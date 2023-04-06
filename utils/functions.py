import zlib
import os
import re

from pathlib import Path

def save_html(soup, expedient):
        path = os.environ['HTML_PATH']
        try:
            os.mkdir(os.environ['HTML_PATH'])
        except:
            pass

        filecode = zlib.crc32(soup.encode('utf-8'))
        filename = normalize_string(expedient) + '-' + str(filecode)
        Path(path + '/' + filename).mkdir(parents=True, exist_ok=True)
        file = open(path + '/' + filename + '/' + filename + '.html', 'w', encoding = 'utf8')
        file.write(str(soup))
        file.close()

def normalize_string(string):
    lower_string = string.lower()
    no_punc_string = re.sub(r'[^\w\s]','_', lower_string)
    no_wspace_string = no_punc_string.replace(' ', '_')
    return no_wspace_string