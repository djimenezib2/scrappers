import sys
import os
import requests

sys.path.append("./../")

def store_runnable(start, end, items, source, type):

    data = {
        'start': start.strftime("%Y-%m-%d, %H:%M:%S"),
        'end': end.strftime("%Y-%m-%d, %H:%M:%S"),
        'duration': str(end - start),
        'items': items,
        'source': source,
        'type': type
    }

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Api-Key" : os.environ["TENDIOS_API_KEY"]
    }

    response = requests.post(os.environ["TENDIOS_API_URL"]+'/v1/runnables', headers=headers, json=data)

