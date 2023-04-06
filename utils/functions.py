import zlib
import os
import re

from pathlib import Path

def normalize_string(string):
    lower_string = string.lower()
    no_punc_string = re.sub(r'[^\w\s]','_', lower_string)
    no_wspace_string = no_punc_string.replace(' ', '_')
    return no_wspace_string