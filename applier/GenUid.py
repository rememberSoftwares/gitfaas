import uuid


class RequestUid:

    @staticmethod
    def generate_uid(r):
        request_uid = "r-" + str(uuid.uuid4())
        r.set(request_uid, "")
        return request_uid


class FunctionUid:

    @staticmethod
    def generate_uid(r, request_uid):
        """
        We create a new Function UID. This UID will then be stored inside redis in a list of Function UIDs (separated
        by '|' ie : "uid1|uid2|uid2")
        The key is a Request UID. A new R UID is created for each call to /publish.
        Each F UID is the concatenation of the R UID + the F UID itself. This allows to retrieve the R UID from
        the F UID.
        For example => <r-xxxx> : f-yyyy-r-xxxx|f-zzzz-r-xxxx.
        Obviously the R UIDs (the concatenated ones and the one acting as key) are all identical.
        A F UID by itself is made of 36 char + 2 char for identification. We use "r-" for R UIDs and "f-" for F UIDs.
        In the end the R UID is made of 38 chars and each F UID is made of 2 * 38 chars + a dash separating them both
        => 77 chars
        :param r: Redis client instance
        :param request_uid: The request UID of the current call to /publish
        :return: A function UID corresponding to the unique run of a lambda
        """
        function_uid = "f-" + str(uuid.uuid4()) + "-" + request_uid
        FunctionUid.add_uid_to_redis(r, request_uid, function_uid)
        return function_uid



    @staticmethod
    def add_uid_to_redis(r, request_uid, function_uid):
        """
        We store the new function UID to the list. Each function UID is separated by a '|'.
        FYI the redis key is the requestUID.
        For instance : "<requestUID>": "<functionUID1>|<functionUID2>"
        :param r: Redis client instance
        :param request_uid: The key pointing to a list of function UIDs inside REDIS
        :param function_uid: The UID to add to the list
        :return:
        """
        FunctionUid.init_uid(r, function_uid)
        redis_f_uid_list = r.get(request_uid).decode("utf-8")

        if redis_f_uid_list is None or redis_f_uid_list == "":
            r.set(request_uid, function_uid)
        else:
            r.set(request_uid, redis_f_uid_list + "|" + function_uid)

    def init_uid(r, function_uid):
        """
        We init the function_uid in redis to allow the route "POST /answer" to update this key. "POST /response" cannot store
        a response in a key that hasn't been initialized first (for security reasons)
        :param r: Redis client instance
        :param function_uid:
        :return:
        """
        r.set(function_uid, "")
