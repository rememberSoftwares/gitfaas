import re
import subprocess
import os
import sys
from enum import Enum, auto
import shutil

from Errors import *

CLONE_FOLDER = "clone_folder"
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


class ApplySubDirs(Enum):
    FOLDER1 = auto()
    FOLDER2 = auto()


class ApplyFolders:

    def __init__(self, notify, volume_mount_path):
        self.notify = notify
        self.volume_mount_path = volume_mount_path
        self.folders_map = {
            ApplySubDirs.FOLDER1: "apply1",
            ApplySubDirs.FOLDER2: "apply2"
        }
        self.current_folder_in_use = ApplySubDirs.FOLDER1
        self.folder_not_in_use = ApplySubDirs.FOLDER2

    def copy_content(self, repo_name, e_folder=None):
        if e_folder is not None: #@todo check type
            e_target_folder = e_folder
        else:
            e_target_folder = self.folder_not_in_use

        # Cleaning folder not in use before staring to use it
        try:
            shutil.rmtree(self._get_folder_path_from_enum(e_target_folder))
        except (NameError, FileNotFoundError):
            pass
        #os.mkdir(self._get_folder_path_from_enum(e_target_folder))

        # Copying git cloned folder to currently unused folder
        shutil.copytree(self.volume_mount_path + "/" + CLONE_FOLDER, self._get_folder_path_from_enum(e_target_folder))

        # Setting copied folder as current folder
        self._toggle_folder_in_use(repo_name)

    def to_full_path(self, e_folder, repo_name):
        # @todo check type of e_folder
        return self.volume_mount_path + "/" + self.folders_map[e_folder] + "/" + repo_name

    def _get_folder_path_from_enum(self, e_folder):
        # @todo check type of e_folder
        return self.volume_mount_path + "/" + self.folders_map[e_folder]

    def _toggle_folder_in_use(self, repo_name):
        """
        If folder 1 is in use then we shift to folder 2. If it's folder 2 in use we shift to folder 1
        Then we notify folder update to the apply container
        :return:
        """
        if self.current_folder_in_use == ApplySubDirs.FOLDER1:
            self.current_folder_in_use = ApplySubDirs.FOLDER2
            self.folder_not_in_use = ApplySubDirs.FOLDER1
        else:
            self.current_folder_in_use = ApplySubDirs.FOLDER1
            self.folder_not_in_use = ApplySubDirs.FOLDER2
        self.notify.folder_in_use(self.to_full_path(self.current_folder_in_use, repo_name))


class Repo(object):

    def __init__(self, repo_url, user_name, token, branch, volume_mount_path,  notify):
        self.firstRun = True
        self.scheme = repo_url.split("://")[0]
        self.repoUrl = repo_url.split("://")[1]
        self.user_name = user_name
        self.token = token
        self.branch = branch
        self.volume_mount_path = volume_mount_path
        self.repoName = self.extract_folder_name_from_git_url()
        self.apply_folders = ApplyFolders(notify, self.volume_mount_path)
        # Tracking previous and current hash representing repo state.
        # If both hashes are different then the repo has been updated otherwise nothing happened
        self.previous_hash = None
        self.current_hash = None

    def _clone_repo(self):
        try:
            os.mkdir(self.volume_mount_path + "/" + CLONE_FOLDER)
        except FileExistsError:
            pass
        os.chdir(self.volume_mount_path + "/" + CLONE_FOLDER)
        command = "git clone -b " + self.branch + " --single-branch " + self.scheme + "://" + self.user_name + ":" + self.token + "@" + self.repoUrl
        output = Exec.run(command)
        Exec.search_for(output, FAILED_GIT_PULL_REGEX)

        try:
            os.chdir(self.volume_mount_path + "/" + CLONE_FOLDER + "/" + self.repoName)
        except FileNotFoundError:
            raise GitUpdateError("No folder was cloned")
        self.firstRun = False

    def _pull_repo(self):
        command = "git pull origin " + self.branch
        output = Exec.run(command)
        Exec.search_for(output, FAILED_GIT_PULL_REGEX)

    def update_repo(self):
        print("Updating repo")
        self.previous_hash = self.current_hash
        if self.firstRun:
            self._clone_repo()
        else:
            self._pull_repo()
        self.current_hash = Repo.get_current_hash()

        if self.has_repo_changed():
            self.apply_folders.copy_content(self.repoName)

    def to_full_path(self, e_folder):
        # @todo check type of e_folder
        return self.volume_mount_path + "/" + self.apply_folders.folders_map[e_folder] + "/" + self.extract_folder_name_from_git_url()

    @staticmethod
    def get_current_hash():
        print("Getting current hash")
        command = "git rev-parse HEAD"
        return (Exec.run(command)[0]).rstrip() #run renvoie un tableau mais moi j'aurais forcement qu'une seule ligne

    def has_repo_changed(self):
        return self.current_hash != self.previous_hash

    """
    def diff(self, hash1, hash2):
        command = "git diff --name-only " + hash1.decode() + " " + hash2.decode()
        return Exec.run(command)
    """

    def extract_folder_name_from_git_url(self):
        split = self.repoUrl.split("/")
        return split[-1].split(".")[0]

