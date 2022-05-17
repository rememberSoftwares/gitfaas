import validators

class InputValuesCheck(object):

    @staticmethod
    def checkPollingTime(value):
        value = int(value)
        if isinstance(value, int) and value > 0:
            return
        else:
            print("Polling time should be an integer > 0")
            raise ValueError

    @staticmethod
    def checkGitUrl(value):
        if validators.url(value):
            return
        else:
            raise ValueError

    @staticmethod
    def checkWorkPath(value):
        if value is not None and len(value) > 1 and value[0] == "/":
            return
        else:
            print(
                "This value should not have been edited. Use default from github. Current value is wrong. Must start with / and be at least one letter long for folder name")
            raise ValueError

    @staticmethod
    def checkGitAuth(username, password):
        if len(username) > 0 and len(password) > 0:
            return True
        else:
            raise ValueError
