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
                print(res.json())
        except Exception as e:
            logging.error(traceback.format_exc())

    def clone_folder_name(self, clone_folder):
        url = 'http://127.0.0.1:5000/folderName?tofu=' + self.tofu_code
        data = {"folderName": clone_folder}
        try:
            print("sending", data)
            res = requests.post(url, json=data)
            if res.ok:
                print(res.json())
        except Exception as e:
            logging.error(traceback.format_exc())

    def manifests_config(self, config):
        url = 'http://127.0.0.1:5000/configUpdate?tofu=' + self.tofu_code
        try:
            print("sending", config)
            x = requests.post(url, json=config)
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
        while alive is False:
            try:
                print("Waiting for proof of life")
                res = requests.get(url)
                print("res = ", str(res))
                return True
            except Exception as e:
                print("Not ready... Trying again in 2 sec")
                time.sleep(2)

