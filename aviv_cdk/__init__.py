__version__='0.0.7'


def __json_load(filename: str) -> dict:
    import json
    with open(filename) as cfgfile:
        return json.load(cfgfile)

def __load_yaml(filename: str) -> object:
    import yaml
    with open(filename, encoding="utf8") as fp:
        with fp.read() as bsfile:
            return yaml.safe_load(bsfile)
