import traceback
import logging
from Errors import *


class ConfigReader(object):

    def __init__(self, config_path):
        self.config_path = config_path

    def load_config_from_fs(self):
        try:
            with open(self.config_path) as f:
                return f.read()
        except Exception as e:
            logging.debug(traceback.format_exc())
            logging.fatal("Configuration file not found. Common value is './config.json' but it may have been set to a different value inside the Helm chart. Current given path is %s" % self.config_path)
            raise GitUpdateError("Configuration file not found")
