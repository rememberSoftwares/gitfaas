import logging
import os

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

    @staticmethod
    def get_redis_expiration_time():
        """
        The expiration time is set inside the helm chart and should be set. If not we default to a 2 days retention.
        Expiration time is used in redis to purge function_uids and request_uids after a specific period of time.
        :return:
        """
        expiration_time = os.environ.get("EXPIRATION_TIME")
        if expiration_time is None:
            logging.warning("Expiration time is not defined. Defaulting to 172800 seconds (2days)")
            return 172800
        if expiration_time.isdigit() is not True:
            raise ValueError(f"Invalid EXPIRATION_TIME. Was expecting integer, got {expiration_time}")
        return int(expiration_time)
