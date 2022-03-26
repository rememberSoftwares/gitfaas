import subprocess
import os
import sys


class Exec(object):

    @staticmethod
    def run(command):
        output = []
        print("command = " + command)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            print(line)
            output.append(line)
        p.wait()
        return output

class Repo(object):

    def __init__(self, repo_url, user_name, token):
        self.firstRun = True
        self.scheme = repo_url.split("://")[0]
        self.repoUrl = repo_url.split("://")[1]
        self.user_name = user_name
        self.token = token
        print("scheme = ", self.scheme, " repo url = ", self.repoUrl, "username = ", self.user_name)

    def _cloneRepo(self):
        print("scheme = ", self.scheme,)
        print(" repo url = ", self.repoUrl,)
        print("username = ", self.user_name)
        GIT_BRANCH = os.environ.get('GIT_PULL_BRANCH', None)
        if GIT_BRANCH is None:
            print("No git branch has been set. Exiting now...")
            sys.exit(1)
        command = "git clone -b " + GIT_BRANCH + " --single-branch " + self.scheme + "://" + self.user_name + ":" + self.token + "@" + self.repoUrl
        print("THE COMMAND = ", command)
        Exec.run(command)
        os.chdir(self.extract_folder_name())
        self.firstRun = False

    def updateRepo(self):
        print("Updating repo")
        if self.firstRun == True:
            self._cloneRepo()
            return
        #@todo prendre la branche en env
        command = "git pull origin master"
        Exec.run(command)

    def getCurrentHash(self):
        print("Getting current hash")
        command = "git rev-parse HEAD"
        return (Exec.run(command)[0]).rstrip() #run renvoie un tableau mais moi j'aurais forcement qu'une seule ligne

    def diff(self, hash1, hash2):
        command = "git diff --name-only " + hash1.decode() + " " + hash2.decode()
        return Exec.run(command)

    def extract_folder_name(self):
        split = self.repoUrl.split("/")
        return split[-1].split(".")[0]

