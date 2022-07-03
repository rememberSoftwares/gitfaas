import logging
import re
import subprocess
import os
import sys
from enum import Enum, auto
import shutil

from Config import CLONE_FOLDER, VOLUME_MOUNT_PATH
from ApplyFolders import UrlType, ApplyFolders
from Exec import Exec, FAILED_GIT_PULL_REGEX
from Errors import *


class RepoFactory(object):

    @staticmethod
    def create_repo(repo_url, username, personal_token, branch, host_key_check, notify):
        url_type = RepoFactory.get_url_type(repo_url)
        if url_type == UrlType.HTTP:
            return RepoHttp(repo_url, username, personal_token, branch, notify)
        elif url_type == UrlType.SSH:
            return RepoSsh(repo_url, branch, host_key_check, notify)

    @staticmethod
    def get_url_type(repo_url): #@todo display warning when using http based urls
        if repo_url.startswith("http://") or repo_url.startswith("https://"):
            return UrlType.HTTP
        elif repo_url.startswith("git@"):
            return UrlType.SSH
        else:
            raise ValueError("URL did not match syntax criteria : Must start by 'http(s)://' or 'ssh@'")


class Repo(object):

    def __init__(self, repo_url, branch, notify):
        self.firstRun = True
        self.repo_url = repo_url
        self.branch = branch
        self.repoName = self.extract_folder_name_from_git_url()
        self.apply_folders = ApplyFolders(notify)
        # Tracking previous and current hash representing repo state.
        # If hashes are different then the repo has been updated otherwise nothing happened
        self.previous_hash = None
        self.current_hash = None

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
        return VOLUME_MOUNT_PATH + "/" + self.apply_folders.folders_map[e_folder] + "/" + self.extract_folder_name_from_git_url()

    @staticmethod
    def get_current_hash():
        print("Getting current hash")
        command = "git rev-parse HEAD"
        return (Exec.run(command)[0]).rstrip() #run renvoie un tableau mais moi j'aurais forcement qu'une seule ligne

    def has_repo_changed(self):
        return self.current_hash != self.previous_hash

    def extract_folder_name_from_git_url(self):
        split = self.repo_url.split("/")
        return split[-1].split(".")[0]


class RepoSsh(Repo):

    def __init__(self, repo_url, branch, host_key_check, notify):
        self.repo_url = repo_url
        self.branch = branch
        self.host_key_check = True if host_key_check == "yes" else False
        self.repo_name = self.extract_folder_name_from_git_url()
        logging.info("Extracted repo name : [%s]" % str(self.repo_name))
        Repo.__init__(self, repo_url, branch, notify)

    def _clone_repo(self):
        if self.host_key_check is False:
            Exec.run("git config --global core.sshCommand 'ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'")
        try:
            os.mkdir(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER)
        except FileExistsError:
            pass
        os.chdir(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER)
        command = "git clone -b " + self.branch + " --single-branch " + self.repo_url
        output = Exec.run(command)
        Exec.search_for(output, FAILED_GIT_PULL_REGEX)

        try:
            os.chdir(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER + "/" + self.repo_name)
        except FileNotFoundError:
            raise GitUpdateError("No folder was cloned")
        self.firstRun = False


class RepoHttp(Repo):

    def __init__(self, repo_url, user_name, token, branch,  notify):
        self.firstRun = True
        self.scheme = repo_url.split("://")[0]
        self.repo_url = repo_url.split("://")[1]
        self.user_name = user_name
        self.token = token
        self.branch = branch
        self.repo_name = self.extract_folder_name_from_git_url()
        logging.info("Extracted repo name : [%s]" % self.repo_name)
        Repo.__init__(self, repo_url, branch, notify)

    def _clone_repo(self):
        try:
            os.mkdir(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER)
        except FileExistsError:
            pass
        os.chdir(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER)
        command = "git clone -b " + self.branch + " --single-branch " + self.scheme + "://" + self.user_name + ":" + self.token + "@" + self.repo_url
        output = Exec.run(command)
        Exec.search_for(output, FAILED_GIT_PULL_REGEX)

        try:
            os.chdir(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER + "/" + self.repo_name)
        except FileNotFoundError:
            raise GitUpdateError("No folder was cloned")
        self.firstRun = False

    def extract_folder_name_from_git_url(self):
        split = self.repo_url.split("/")
        return split[-1].split(".")[0]

