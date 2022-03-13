import json
import os
import time
import requests
import traceback
import logging


class Notify(object):

    @staticmethod
    def clone_folder_name(clone_folder):
        url = 'http://127.0.0.1:5000/folderName'
        data = {"folderName": clone_folder}
        try:
            print("sending", data)
            res = requests.post(url, json=data)
            if res.ok:
                print(res.json())
        except Exception as e:
            logging.error(traceback.format_exc())

    @staticmethod
    def manifests_config(config):
        url = 'http://127.0.0.1:5000/configUpdate'
        try:
            print("sending", config)
            x = requests.post(url, json=config)
        except Exception as e:
            logging.error(traceback.format_exc())


    @staticmethod
    def pid():
        url = 'http://127.0.0.1:5000/pidUpdate'
        try:
            x = requests.post(url, json={"pid": os.getpid()})
        except Exception as e:
            logging.error(traceback.format_exc())



    @staticmethod
    def wait_for_ready_status():
        alive = False
        url = 'http://127.0.0.1:5000/alive'
        while alive is False:
            try:
                print("Waiting for proof of life")
                res = requests.get(url)
                return True
            except Exception as e:
                print("Not ready... Trying again in 2 sec")
                time.sleep(2)

