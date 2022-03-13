import os
import signal
import time
import sys
import sh

from InputValuesCheck import *
from Repo import Repo
from Notify import *
from ConfigReader import *

POLLING_TIME = os.environ.get('POLLING_TIME', 1)
GIT_URL = os.environ.get("GIT_URL", None)
WORK_PATH = os.environ.get("WORK_PATH", None)
GIT_USER_NAME = os.environ.get("GIT_USER_NAME", None)
GIT_PERSONAL_TOKEN = os.environ.get("GIT_PERSONAL_TOKEN", None)
print("auth = ", GIT_USER_NAME, GIT_PERSONAL_TOKEN)


def receive_signal(signal_number, frame):
    print('Received:', signal_number)
    if signal_number == 10:
        repo_refresh(last_hash)


def repo_refresh(previous_hash):
    repo.updateRepo()
    current_hash = repo.getCurrentHash()
    if current_hash != previous_hash:
        Notify.manifests_config(config_reader.load_config_from_fs())
        previous_hash = current_hash
    return previous_hash

print("pid", os.getpid())

try:
    check = InputValuesCheck()
    check.checkPollingTime(POLLING_TIME)
    check.checkGitUrl(GIT_URL)
    check.checkWorkPath(WORK_PATH)
    check.checkGitAuth(GIT_USER_NAME, GIT_PERSONAL_TOKEN)
    POLLING_TIME = int(POLLING_TIME)
except ValueError:
    print("EXITING !")
    sys.exit()

os.chdir(WORK_PATH)
config_reader = ConfigReader()
repo = Repo(GIT_URL, GIT_USER_NAME, GIT_PERSONAL_TOKEN)
config = None
last_hash = None

Notify.wait_for_ready_status()
Notify.clone_folder_name(repo.extract_folder_name())
Notify.pid()
signal.signal(signal.SIGUSR1, receive_signal)

while True:
    last_hash = repo_refresh(last_hash)
    print("Waiting !")
    time.sleep(POLLING_TIME * 60)
