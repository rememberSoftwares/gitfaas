import logging


class Report:

    def __init__(self):
        self.request_uid = None
        self.applies = []
        self.master_error = False

    def create_report(self, error, absolute_path, message):
        if error is True:
            self.master_error = True
        try:
            absolute_path = Report.anonymise_path(absolute_path)
        except ValueError as e:
            logging.WARN(str(e))
        self.applies.append({"error": error, "path": absolute_path, "message": message})

    def set_request_uid(self, request_uid):
        self.request_uid = request_uid

    def to_json(self):
        return {"requestUid": self.request_uid, "applies": self.applies, "error": self.master_error}

    @staticmethod
    def anonymise_path(path):
        split = path.split("/")
        if len(split) < 3:
            raise ValueError("Path doesn't look right")
        stripped = split[2:]
        return "/".join(stripped)
