import json
import os
import time
import uuid
import requests
import traceback
import logging


class Notify(object):

    def __init__(self):
        """
        @tofu_code is generated here and will be used to authenticate against the Apply container.
        First call will give this tofu_code to Apply container. All subsequent calls must give have the tofu code to be
        authenticated. Clients that do not give the right code will receive 404 (preventing attackers to discover too
        much of the API).
        """
        self.tofu_code = str(uuid.uuid4())

    def set_tofu_code(self):
        url = 'http://127.0.0.1:5000/tofuAuth?tofu=' + self.tofu_code
        try:
            res = requests.post(url)
            if res.ok:
                logging.debug("Response from /tofuAuth : %s" % str(res.json()))
        except Exception as e:
            logging.error(traceback.format_exc())

    def folder_in_use(self, full_path):
        url = 'http://127.0.0.1:5000/folderInUse?tofu=' + self.tofu_code
        data = {"path": full_path}
        try:
            logging.debug("Sending path of folder in use to Apply container : %s", str(data))
            res = requests.post(url, json=data)
            if res.ok:
                logging.debug("Response from /folderInUse : %s" % str(res.json()))
        except Exception as e:
            logging.error(traceback.format_exc())

    def manifests_config(self, config):
        url = 'http://127.0.0.1:5000/configUpdate?tofu=' + self.tofu_code
        try:
            logging.debug("Sending manifest config to Apply container : %s", str(config))
            requests.post(url, json=config)
        except Exception as e:
            logging.error(traceback.format_exc())

    def current_proc_pid(self):
        url = 'http://127.0.0.1:5000/pidUpdate?tofu=' + self.tofu_code
        try:
            x = requests.post(url, json={"pid": os.getpid()})
        except Exception as e:
            logging.error(traceback.format_exc())

    def wait_for_ready_status(self):
        alive = False
        url = 'http://127.0.0.1:5000/alive'
        logging.info("Waiting for proof of life")
        while alive is False:
            try:
                requests.get(url)
                return True
            except Exception as e:
                logging.info("Not ready... Trying again in 5 sec")
                time.sleep(5)

    def master_error(self, reason):
        logging.info("reason = %s" % str(reason))
        url = 'http://127.0.0.1:5000/activateMasterError?tofu=' + self.tofu_code
        try:
            requests.post(url, json={"reason": str(reason)})
        except Exception as e:
            logging.error(traceback.format_exc())

