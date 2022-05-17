import os
import signal
import time
import sys
import sh
import logging

from InputValuesCheck import *
from Repo import Repo
from Notify import *
from ConfigReader import *
from Errors import *

AVAILABLE_LOG_LEVELS = ["DEBUG", "INFO", "WARN"]

POLLING_TIME = os.environ.get('POLLING_TIME', 1)
GIT_URL = os.environ.get("GIT_URL", None)
VOLUME_MOUNT_PATH = os.environ.get("VOLUME_MOUNT_PATH", None)
GIT_USER_NAME = os.environ.get("GIT_USER_NAME", None)
GIT_PERSONAL_TOKEN = os.environ.get("GIT_PERSONAL_TOKEN", None)
GIT_BRANCH = os.environ.get("GIT_PULL_BRANCH", "main")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

logger = logging.getLogger('dev')
if LOG_LEVEL not in AVAILABLE_LOG_LEVELS:
    LOG_LEVEL = "INFO"
    print("Invalid value given to LOG_LEVEL. Defaulting to level : INFO")
logger.setLevel(getattr(logging, LOG_LEVEL))


def receive_signal(signal_number, frame):
    print('Received:', signal_number)
    if signal_number == 10:
        repo_refresh()


def repo_refresh():
    try:
        repo.update_repo()
    except GitUpdateError as err:
        logging.fatal(str(err))
        return

    if repo.has_repo_changed():
        notify.manifests_config(config_reader.load_config_from_fs())

try:
    check = InputValuesCheck()
    check.checkPollingTime(POLLING_TIME)
    check.checkGitUrl(GIT_URL)
    check.checkWorkPath(VOLUME_MOUNT_PATH)
    check.checkGitAuth(GIT_USER_NAME, GIT_PERSONAL_TOKEN)
    POLLING_TIME = int(POLLING_TIME)
except ValueError:
    print("EXITING !")
    sys.exit()

config_reader = ConfigReader()
notify = Notify()
repo = Repo(GIT_URL, GIT_USER_NAME, GIT_PERSONAL_TOKEN, GIT_BRANCH, VOLUME_MOUNT_PATH, notify)
config = None

notify.wait_for_ready_status()
notify.set_tofu_code()
notify.current_proc_pid()
signal.signal(signal.SIGUSR1, receive_signal)

while True:
    repo_refresh()
    print("Waiting !")
    time.sleep(POLLING_TIME * 60)
