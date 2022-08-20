import os
import signal
import time
import sys
import logging

from InputValuesCheck import *
from Repo import RepoFactory
from Notify import *
from ConfigReader import *
from Errors import *
from Config import AVAILABLE_LOG_LEVELS

POLLING_INTERVAL = os.environ.get('POLLING_INTERVAL', 1)
GIT_REPO_URL = os.environ.get("GIT_URL", None)
GIT_USER_NAME = os.environ.get("GIT_USER_NAME", None)
GIT_PERSONAL_TOKEN = os.environ.get("GIT_PERSONAL_TOKEN", None)
GIT_BRANCH = os.environ.get("GIT_PULL_BRANCH", "main")
GIT_USE_SSH_KEY = os.environ.get("GIT_USE_SSH_KEY", None)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
GIT_STRICT_HOST_KEY_CHECKING = os.environ.get("GIT_STRICT_HOST_KEY_CHECKING", "yes")
APPLY_CONFIG_PATH = os.environ.get("APPLY_CONFIG_PATH", "config.json")

if LOG_LEVEL not in AVAILABLE_LOG_LEVELS:
    LOG_LEVEL = "INFO"
    print("WARNING:root:Invalid value given to LOG_LEVEL. Defaulting to level : INFO")


logging.basicConfig()
logging.getLogger().setLevel(getattr(logging, LOG_LEVEL))

logging.error("-----> ERROR")
logging.warning("------> WARNING")
logging.info("------> INFO")
logging.debug("-----> DEBUG")

logging.info("Running Git (container) version : %s" % os.environ.get("VERSION", "?"))


def receive_signal(signal_number, frame):
    logging.info('Received signal to refresh from Apply container: %s' % str(signal_number))
    if signal_number == 10:
        repo_refresh()


def repo_refresh():
    try:
        repo.update_repo()
    except GitUpdateError as err:
        logging.fatal(str(err))
        return

    if repo.has_repo_changed():
        try:
            notify.manifests_config(config_reader.load_config_from_fs())
        except GitUpdateError as err:
            notify.master_error(str(err))


try:
    check = InputValuesCheck()
    check.check_polling_time(POLLING_INTERVAL)
    check.check_git_url(GIT_REPO_URL, GIT_USE_SSH_KEY)
    check.check_git_auth(GIT_USER_NAME, GIT_PERSONAL_TOKEN, GIT_USE_SSH_KEY)
    check.check_git_strict_host_key_checking(GIT_STRICT_HOST_KEY_CHECKING)
    POLLING_INTERVAL = int(POLLING_INTERVAL)
except ValueError as err:
    logging.info(err)
    logging.fatal("Exiting...")
    sys.exit()

config_reader = ConfigReader(APPLY_CONFIG_PATH)
notify = Notify()
repo = RepoFactory.create_repo(GIT_REPO_URL, GIT_USER_NAME, GIT_PERSONAL_TOKEN, GIT_BRANCH, GIT_STRICT_HOST_KEY_CHECKING, notify)
config = None

notify.wait_for_ready_status()
notify.set_tofu_code()
notify.current_proc_pid()
signal.signal(signal.SIGUSR1, receive_signal)

while True:
    repo_refresh()
    logging.info("Waiting specified time : %s seconds" % (POLLING_INTERVAL * 60))
    time.sleep(POLLING_INTERVAL * 60)
