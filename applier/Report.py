class Report:

    def __init__(self):
        self.request_uid = None
        self.applies = []
        self.master_error = False

    def create_report(self, error, absolute_path, message):
        if error is True:
            self.master_error = True
        self.applies.append({"error": error, "path": absolute_path, "message": message})

    def set_request_uid(self, request_uid):
        self.request_uid = request_uid

    def to_json(self):
        return {"requestUid": self.request_uid, "applies": self.applies, "error": self.master_error}
