import traceback
import logging

class ConfigReader(object):

    def __init__(self):
        self.CONFIG_PATH = "config.json"

    def load_config_from_fs(self):
        try:
            with open(self.CONFIG_PATH) as f:
                return f.read()
        except Exception as e:
            logging.error(traceback.format_exc())

