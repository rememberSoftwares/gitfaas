from enum import Enum, auto
import shutil

from Config import VOLUME_MOUNT_PATH, CLONE_FOLDER

"""
The repo is cloned in '/pod-data/clone_folder'. It will be pulled periodically.
Right after initial pull a folder '/pod-data/apply1' is created and the content of 'clone_folder' is copied into it.
We then notify the Apply container that all `kubectl apply` should be done in apply1.

Next we periodically pull the repo from clone_folder. If something changed we create a folder '/pod-data/apply2'.
The content of 'clone_folder' is copied into 'apply2' and the Apply container is then notified to apply files in this folder instead.

Each time a new modification is pulled the repo is copied in the 2 folders (apply1 / apply2) one time after the other.
This is to make sure that the Apply container will no apply some YAML configuration while GIT is making modifications to
the files. That's why we copy the updated repo inside a subfolder and then and only then do we notify the Apply container
that it can start applying files from the specified folder.

Update in clone_folder => CP to apply1 => notify apply1 folder is ready to be used => pull updates
=> if updates: true => CP updated clone_folder to apply2 => notify that apply2 is ready to be used => pull updates => etc
"""


class ApplySubDirs(Enum):
    FOLDER1 = auto()
    FOLDER2 = auto()


class UrlType(Enum):
    HTTP = auto()
    SSH = auto()


class ApplyFolders:

    def __init__(self, notify):
        self.notify = notify
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

        # Cleaning folder not in use before starting to use it
        try:
            shutil.rmtree(self._get_folder_path_from_enum(e_target_folder))
        except (NameError, FileNotFoundError):
            pass
        #os.mkdir(self._get_folder_path_from_enum(e_target_folder))

        # Copies git cloned folder to currently unused folder
        shutil.copytree(VOLUME_MOUNT_PATH + "/" + CLONE_FOLDER, self._get_folder_path_from_enum(e_target_folder))

        # Setting copied folder as current folder
        self._toggle_folder_in_use(repo_name)

    def to_full_path(self, e_folder, repo_name):
        # @todo check type of e_folder
        return VOLUME_MOUNT_PATH + "/" + self.folders_map[e_folder] + "/" + repo_name

    def _get_folder_path_from_enum(self, e_folder):
        # @todo check type of e_folder
        return VOLUME_MOUNT_PATH + "/" + self.folders_map[e_folder]

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