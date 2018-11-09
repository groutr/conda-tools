import json
from os.path import exists

config = None

def load_config(path):
    if exists(path):
        with open(path, 'r') as cin:
            x = json.load(cin)

    global config
    config = config or x

def save_config(path, config):
    with open(path, 'w') as cout:
        json.dump(config, cout)
