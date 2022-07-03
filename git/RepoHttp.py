import re
import subprocess
import os
import sys
from enum import Enum, auto
import shutil

from Errors import *
from Repo import *

class HttpRepo(Repo):

    def __init__(self, repo_url, user_name, token, branch, volume_mount_path,  notify):
        self.firstRun = True
        self.url_type =
        self.scheme = repo_url.split("://")[0]
        self.repoUrl = repo_url.split("://")[1]
        self.user_name = user_name
        self.token = token
        self.branch = branch
        self.volume_mount_path = volume_mount_path
        self.repoName = self.extract_folder_name_from_git_url()
        self.apply_folders = ApplyFolders(notify, self.volume_mount_path)
        # Tracking previous and current hash representing repo state.
        # If hashes are different then the repo has been updated otherwise nothing happened
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

    def extract_folder_name_from_git_url(self):
        split = self.repoUrl.split("/")
        return split[-1].split(".")[0]

