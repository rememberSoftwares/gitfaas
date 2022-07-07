import logging
import subprocess
import base64
import sys
import re

SUCCESSFUL_APPLY_REGEX = "\w+\/.* (?:created|unchanged|configured)(?:\\n)?$"

class ApplyError(Exception):
    """
    Exception class
    Raised when we find 'error' keyword in the output of kubectl apply, which cannot be good
    """
    pass

class Exec(object):

    @staticmethod
    def run(command):
        output = []
        logging.info("Executing command % s", command)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        logging.debug("Start : command output")
        for line in p.stdout.readlines():
            logging.debug("%s" % line)
            output.append(line.decode("utf-8"))
        logging.debug("End : command output")
        p.wait()
        return output

class Kubernetes(object):

    @staticmethod
    def apply_from_stdin(yaml_to_apply):
        b64_yaml = base64.b64encode(bytes(yaml_to_apply, 'utf-8'))
        logging.debug("Yaml to apply : \n%s" % str(yaml_to_apply))
        output = Exec.run("echo " + b64_yaml.decode("utf-8") + " | base64 -d | kubectl apply -f -")
        for line in output:
            match = re.search(SUCCESSFUL_APPLY_REGEX, line)
            if match is None:
                raise ApplyError("Applying file did not return expected results : " + str(line))
    """
    @staticmethod
    def apply(path):
        print("Applying file = " + path)
        Exec.run("kubectl apply -f " + path)
    """

    @staticmethod
    def delete(config):
        logging.info("Deleting %s" % config.path)
        Exec.run("kubectl delete -f " + config.path)

    @staticmethod
    def deleteBatch(configs):
        for config in configs:
            logging.info("Deleting %s" % config.path)
            Exec.run("kubectl delete " + config.kind + " " + config.name + " -n " + config.namespace)

    @staticmethod
    def applyBatch(configs):
        for config in configs:
            logging.info("Applying %s" % config.path)
            Exec.run("kubectl apply -f " + config.path)
