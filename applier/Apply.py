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
        print("command = " + command, file=sys.stderr)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print(line, file=sys.stderr)
            output.append(line.decode("utf-8"))
        p.wait()
        return output

class Kubernetes(object):

    @staticmethod
    def apply_from_stdin(yaml_to_apply):
        b64_yaml = base64.b64encode(bytes(yaml_to_apply, 'utf-8'))
        print("Applying yaml = " + str(yaml_to_apply), file=sys.stderr)
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
        print("Deleting = " + config.path)
        Exec.run("kubectl delete -f " + config.path)

    @staticmethod
    def deleteBatch(configs):
        for config in configs:
            print("Deleting = " + config.path)
            Exec.run("kubectl delete " + config.kind + " " + config.name + " -n " + config.namespace)

    @staticmethod
    def applyBatch(configs):
        for config in configs:
            print("Applying file = " + config.path)
            Exec.run("kubectl apply -f " + config.path)