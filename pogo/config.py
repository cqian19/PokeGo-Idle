from configparser import ConfigParser
import os

CONFIG_PATH = "../config.ini"
DEFAULT = {
    'Config': {
        'username': '',
        'key': '',
        'location': '',
        'method': '',
        'walkspeed': 2.6,
        'searchRadius': 70,
        'requestDelay': 0.5,
        'discardCP': 200,
        'discardIV': 80
    }
}

class Config():

    def __init__(self, logger):
        self.logger = logger
        self.config = ConfigParser()
        self.config.optionxform=str
        self.data = DEFAULT.copy()
        try:
            with open(CONFIG_PATH) as file:
                self.config.read_file(file)
            if self.config.has_section('Config'):
                self.update_config(self.get_config())
            else:
                self.init_config()
        except IOError as e:
            self.init_config()

    def get(self, attr):
        if attr in self.data['Config']:
            return self.data['Config'][attr]
        self.logger.error("Could not get attr " + attr + " from config.")

    def get_float(self, attr):
        return float(self.get(attr))

    def get_int(self, attr):
        return int(self.get(attr))

    def get_config(self):
        return dict(self.config.items())['Config']

    def update_config(self, data):
        data = data.get('Config', data)
        self.data['Config'].update(data)
        self.write_config()

    def write_config(self):
        print(self.data)
        self.config.read_dict(self.data)
        mode = 'w' if os.path.exists(CONFIG_PATH) else 'w+'
        with open(CONFIG_PATH, mode) as file:
            self.config.write(file)

    def init_config(self):
        self.write_config()


