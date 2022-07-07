import sys
from enum import Enum, auto
import re
import os

# Name of the env variable containing a list of ressources to ban (aka will not be applied by gitfaas)
ENV_BANNED_KUBE_RESSOURCES = "BANNED_KUBE_RESS"
BANNED_RESSOURCE_REGEX_TEMPLATE = "kind *\: *<KUBE_RESS_REPLACED_AT_RUNTIME>"
SUB_RESSOURCE_REGEX_TEMPLATE = "kind *\:"


class Source(Enum):
    MANIFEST = auto()
    REQUEST_PARAM = auto()


class DangerousKeyword(Exception):
    """
    Exception class
    Raised when a dangerous keyword has been detected inside a yaml payload. ie RBAC stuff like 'role' etc
    """
    pass

    def __init__(self, message, source): #@todo check type of source to ensure it is of type enum Source
        self.source = source
        self.message = message
        super().__init__(self.message)


class SafeMode:

    def __init__(self):
        self.banned = []
        self._get_banned_strings_from_env()

    def _get_banned_strings_from_env(self):
        banned_res_list = os.environ[ENV_BANNED_KUBE_RESSOURCES]
        if banned_res_list is not None:
            split = banned_res_list.split(" ")
            self.banned = list(map(str.lower, split))

    def check_for_banned_ressources(self, haystack):
        haystack = haystack.lower()
        for ban_ressource in self.banned:
            regex = BANNED_RESSOURCE_REGEX_TEMPLATE.replace("<KUBE_RESS_REPLACED_AT_RUNTIME>", ban_ressource)
            if self._find_match(regex, haystack):
                raise DangerousKeyword("Dangerous keyword has been detected in payload : " + str(ban_ressource), Source.MANIFEST)

    def check_for_sub_ressource(self, haystack):
        """
        In /publish, the user can pass custom params that will be templatized in their manifest at runtime. To make sure
        they dont pass a full manifest in there we deny the word "kind" and the use of "\n"
        :param haystack: Search is performed on the content of this variable
        :return:
        """
        if self._find_match(SUB_RESSOURCE_REGEX_TEMPLATE, haystack):
            raise DangerousKeyword("A sub ressource has been detected. Word 'kind' is forbidden for security reasons.", Source.REQUEST_PARAM)
        if "\n" in haystack:
            raise DangerousKeyword("A newline has been detected. This is forbidden for security reasons.", Source.REQUEST_PARAM)

    def _find_match(self, regex, haystack):
        x = re.search(regex, haystack)
        if x is None:
            return False
        return True
