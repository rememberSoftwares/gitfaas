import validators


class InputValuesCheck(object):

    @staticmethod
    def check_polling_time(value):
        value = int(value)
        if isinstance(value, int) and value > 0:
            return
        else:
            print("Polling time should be an integer > 0")
            raise ValueError

    @staticmethod
    def check_git_url(value, use_ssh_key):
        """
        Checking validity of url. Only http URLs can be check using validators. If the mode is ssh then  we can only
        check for emptiness
        :param value:
        :param use_ssh_key:
        :return:
        """
        if use_ssh_key.lower() == "yes":
            if len(value) <= 0:
                raise ValueError("SSH Git URL is invalid (evaluated as 0 length)")
            return
        else:
            if validators.url(value):
                return
            else:
                raise ValueError("HTTP Git URL is invalid (does not look like a url")

    @staticmethod
    def check_work_path(value):
        if value is not None and len(value) > 1 and value[0] == "/":
            return
        else:
            print(
                "This value should not have been edited. Use default from github. Current value is wrong. Must start with / and be at least one letter long for folder name")
            raise ValueError

    @staticmethod
    def check_git_auth(username, personal_token, use_ssh_key):
        """
        If we don't use sshkey then we must have a valid username and personal_token
        :param username:
        :param personal_token:
        :param use_ssh_key:
        :return:
        """
        if use_ssh_key == "yes":
            return
        elif use_ssh_key == "no" and len(username) > 0 and len(personal_token) > 0:
            return
        else:
            print("Git auth error")
            raise ValueError

    @staticmethod
    def check_git_strict_host_key_checking(value):
        if value == "yes" or value == "no":
            return
        else:
            raise ValueError("StrictHostKey env variable must be set to 'yes' or 'no'")

