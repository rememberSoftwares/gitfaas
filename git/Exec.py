import logging
import re
import subprocess
import sys

from Errors import *

FAILED_GIT_PULL_REGEX = "fatal\: couldn\'t find remote|fatal\: repository|fatal\: Remote branch .* not found in upstream"


class Exec(object):

    @staticmethod
    def run(command, show_command=True, info_msg=None):
        output = []
        if show_command:
            logging.info("Executing command % s", command)
        else:
            logging.info("Executing a command but output is disabled")
        if info_msg is not None:
            logging.info("Exec info message : %s" % info_msg)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.debug("Start : command output")
        for line in p.stdout.readlines():
            logging.debug("%s" % line)
            output.append(line.decode("utf-8"))
        logging.debug("End : command output")
        p.wait()
        return output

    @staticmethod
    def search_for(output, needle):
        for line in output:
            match = re.search(needle, line)
            if match:
                raise GitUpdateError("Git update failed : " + str(line))