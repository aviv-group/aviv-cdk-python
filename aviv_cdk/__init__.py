__version__='0.0.2'

import json

def __json_load(filename: str) -> dict:
    with open(filename) as cfgfile:
        content = json.load(cfgfile)
    return content
