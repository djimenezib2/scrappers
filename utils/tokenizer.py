import sys
import io
import re
from typing import *

def tokenize(string:str) -> List[str]:
    string = string.lower()\
        .replace("á", "a")\
        .replace("é", "e")\
        .replace("í", "i")\
        .replace("ó", "o")\
        .replace("ú", "u")\
        .replace("à", "a")\
        .replace("è", "e")
    tokens = [token.strip(" \"\n\r") for token in re.split(r"-|\(|\)|,|/", string)]
    return tokens

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"{sys.argv[0]}: input output")
        sys.exit(1)
    tokenDB:List[str] = [""]
    inputPath = sys.argv[1]
    outputPath = sys.argv[2]
    fdi:io.TextIOBase = io.open(inputPath, "r")
    fdo:io.TextIOBase = io.open(outputPath, "w")
    with fdi, fdo:
        while line := fdi.readline():
            tokens = tokenize(line)
            print(repr(tokens))
            for token in tokens:
                if not token in tokenDB:
                    fdo.write(token + "\n")
                    tokenDB.append(token)