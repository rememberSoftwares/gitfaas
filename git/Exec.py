import re
import subprocess
import sys
from Errors import *

FAILED_GIT_PULL_REGEX = "fatal\: couldn\'t find remote|fatal\: repository|fatal\: Remote branch .* not found in upstream"


class Exec(object):

    @staticmethod
    def run(command):
        output = []
        print("command = " + command, file=sys.stderr)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print(line, file=sys.stderr)
            output.append(line.decode("utf-8"))
        p.wait()
        return output

    @staticmethod
    def search_for(output, needle):
        for line in output:
            match = re.search(needle, line)
            if match:
                raise GitUpdateError("Git update failed : " + str(line))