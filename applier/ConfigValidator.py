class InvalidConfig(Exception):
    """
    Exception class
    Raised when something doesn't look right in the JSON config written by the user
    """
    pass


class ConfigValidator:

    @staticmethod
    def check_for_path_escape(config_json):
        """
        To ensure that a hacker won't try to move around the filesystem we block the use of /../
        :param config_json:
        :return:
        """
        if ".." in config_json:
            raise InvalidConfig("String '..' is denied for security reasons")
