import signal
import time

from flask import Flask, render_template, jsonify, request, abort
from waitress import serve
import sys
import json
import os
import chevron
import base64
import uuid
import traceback
import logging
import redis
import re
from functools import wraps

from Apply import Kubernetes
from SafeMode import *
from Apply import ApplyError
from ConfigValidator import *
from Report import Report
from GenUid import *

# Logging options for the app. Choosing for instance INFO will only print logging.info(...) and above outputs
AVAILABLE_LOG_LEVELS = ["DEBUG", "INFO", "WARN"]
# Contains an auto-generated password sent by the Git container at startup. This should not be modified during runtime.
g_tofu_code = None

# Getting current log level
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
if LOG_LEVEL not in AVAILABLE_LOG_LEVELS:
    LOG_LEVEL = "INFO"
    print("WARNING:root:Invalid value given to LOG_LEVEL. Defaulting to level : INFO")
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m-%d %H:%M')
logging.getLogger().setLevel(getattr(logging, LOG_LEVEL))

app = Flask(__name__)

print(f"Log level should be {LOG_LEVEL}")
logging.error("ERROR logs are shown")
logging.warning("WARNING logs are shown")
logging.info("INFO logs are shown")
logging.debug("DEBUG logs are shown")

REDIS_EXPIRATION_TIME = ConfigValidator.get_redis_expiration_time()


def wait_for_redis():
    ping = False
    while ping == False:
        try:
            ping = r.ping()
        except:
            pass
        logging.info(str("Waiting for redis to be alive"))
        time.sleep(4)


def ready_to_use():
    return r.get("current_config") is not None and r.get("folder_in_use") is not None and r.get("master_error").decode("utf-8") == "False"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get('tofu') == g_tofu_code:
            return f(*args, **kwargs)
        else:
            abort(404)
    return decorated_function


@app.route('/alive', methods=["GET"])
def alive():
    return jsonify({"alive": True})


@app.route('/tofuAuth', methods=["POST"])
def tofu_auth():
    global g_tofu_code
    g_tofu_code = request.args.get('tofu')
    return jsonify({"alive": True})


@app.route('/folderInUse', methods=["POST"])
@login_required
def update_folder_name():
    folder_name = request.json["path"]
    r.set("folder_in_use", folder_name)
    return jsonify({"error": False})


@app.route('/pidUpdate', methods=["POST"])
@login_required
def update_pid():
    r.set("git_pid", int(request.json["pid"]))
    return jsonify({"error": False})


@app.route('/activateMasterError', methods=["POST"])
@login_required
def activate_master_error():
    try:
        logging.error("Entering master error mode")
        logging.error(str(type(request.json)))
        if "reason" not in request.json:
            logging.error("Missing reason text field")
            return jsonify({"error": True, "message": "Missing reason text field"})
        r.set("master_error", "True")
        r.set("last_master_error_description", request.json["reason"])
        logging.warning("Application entering error mode with reason : %s" % request.json["reason"])
    except Exception as e:
        logging.error("/activateMasterError : Loading JSON failed")
        return jsonify({"error": True, "message": "Loading JSON failed"})
    return jsonify({"error": False})


@app.route('/configUpdate', methods=["POST"])
@login_required
def update_config():
    """
    Gets the config from the git repo
    :return:
    """
    try:
        json_config = json.loads(request.json)
        for topic_config in json_config["topics"]:
            for file_path in topic_config["configs"]: #@todo remplacer par "manifests"
                ConfigValidator.check_for_path_escape(file_path)
        r.set("current_config", request.json)
        r.set("master_error", "False")
        return jsonify({"error": False, "message": ""})

    except InvalidConfig as err:
        logging.error(str(err))
        r.set("master_error", "True")
        r.set("last_master_error_description", str(err))

    except Exception as e:
        r.set("master_error", "True")
        err_str = "Loading config.json failed. Check common JSON issues like missing comas etc"
        logging.error(err_str)
        logging.debug(traceback.format_exc())
        r.set("last_master_error_description", err_str)

    return {"error": True, "message": "Loading config failed"}


@app.route('/refresh', methods=["GET"])
def refresh():
    git_pid = r.get("git_pid")
    if git_pid is None:
        return jsonify({"error": True, "message": "Pid of GIT container unknown. This should have been auto configured on startup"})
    os.kill(int(git_pid), signal.SIGUSR1)
    return jsonify({"error": False})

"""
Stores inside redis the response of a faas function.
function_uid's key in redis is init by publish() : If the user gives an unknown uid then the value from redis will be None and the
request will be denied.
"""
@app.route('/response/<function_uid>', methods=["POST"])
def post_response(function_uid):
    if len(function_uid) != 77 or re.match(r"f\-\w+\-\w+\-\w+\-\w+\-\w+\-r-\w+-\w+-\w+-\w+-\w+", function_uid) is False or r.get(function_uid) is None:
        return jsonify({"error": True, "message": "Function uid is invalid. Are you sure you want to GET this ressource and not POST a new one ?"})

    elif request.content_type is None or request.content_type.startswith('text/plain'):
        message_text = str(request.data.decode('utf-8'))

    elif request.content_type.startswith('application/json'):
        try:
            message_text = json.dumps(request.json)
        except Exception as e:
            logging.error("Incoming request treated as JSON by Flask. Error while converting json to string : %s" % str(e))
            return jsonify({"error": True, "message": "Incorrect JSON : " + str(e)}), 400

    else:
        return jsonify({"error": True, "message": "Given content type is not supported :" + str(request.content_type) + ". Please use application/json, text/plain or nothing"}), 406

    if message_text is None or message_text == "":
        return jsonify({"error": True, "message": "Data field in POST request cannot be empty."})

    b64_msg = base64.b64encode(bytes(message_text, 'utf-8'))
    r.set(function_uid, b64_msg, ex=REDIS_EXPIRATION_TIME)
    logging.info("Setting response for function %s" % function_uid)
    return jsonify({"error": False, "message": "Response stored correctly"})


@app.route('/response/<request_uid>', methods=["GET"])
def get_response(request_uid):
    if len(request_uid) != 38 or re.match(r"r-\w+-\w+-\w+-\w+-\w+", request_uid) is False:
        return jsonify({"error": True, "message": "Function uid is invalid", "responses": []})

    function_uids = r.get(request_uid)
    if function_uids is None:
        return jsonify({"error": False, "responses": []})

    function_uids_list = function_uids.decode("utf-8").split("|")
    responses_aggregation = []

    for function_uid in function_uids_list:
        logging.debug("Function uid %s" % str(function_uid))
        function_response = r.get(function_uid)
        responses_aggregation.append(None if (function_response is None or function_response.decode("utf-8") == "") else function_response.decode("utf-8"))
    return jsonify({"error": False, "responses": responses_aggregation})


@app.route('/publish/<topic>', methods=["POST"])
def publish(topic):
    if r.get("master_error").decode("utf-8") == "True":
        return jsonify({"error": True, "message": "App state is in ERROR : " + r.get("last_master_error_description").decode("utf-8")}), 409

    report = Report()
    logging.info("Topic : %s" % topic)
    logging.debug("Folder in use : %s" % r.get("folder_in_use"))

    logging.debug("Getting content-type = %s" % str(request.content_type))

    if request.content_type is None or request.content_type.startswith('text/plain'):
        message_text = str(request.data.decode('utf-8'))

    elif request.content_type.startswith('application/json'):
        try:
            message_text = json.dumps(request.json)
        except Exception as e:
            logging.error("Incoming request treated as JSON by Flask. Error while converting json to string : %s" % str(e))
            return jsonify({"error": True, "message": "Incorrect JSON : " + str(e)}), 400

    else:
        return jsonify({"error": True, "message": "Given content type is not supported :" + str(request.content_type) + ". Please use application/json, text/plain or nothing"}), 406

    if ready_to_use():
        current_config = json.loads(r.get("current_config"))
        request_uid = RequestUid.generate_uid(r)
        report.set_request_uid(request_uid)
        for current_topic in current_config["topics"]:
            if current_topic["name"] == topic:
                for file_path in current_topic["configs"]:
                    absolute_path = r.get("folder_in_use").decode("utf-8") + "/" + file_path
                    request_params = request.args.to_dict()
                    function_uid = FunctionUid.generate_uid(r, request_uid)
                    try:
                        yaml_to_apply = templatize_yaml(absolute_path, function_uid, message_text, request_params, topic)
                        sf = SafeMode()
                        sf.check_for_banned_ressources(yaml_to_apply)
                        sf.check_for_sub_ressource(str(request_params))
                        Kubernetes.apply_from_stdin(yaml_to_apply)
                        report.create_report(False, absolute_path, "Applied successfully")

                    except FileNotFoundError as err:
                        logging.warning("File to apply not found : %s" % str(err))
                        report.create_report(True, absolute_path, str(err))

                    except DangerousKeyword as err:
                        logging.warning("%s" % str(err))
                        if err.source == Source.REQUEST_PARAM:
                            return jsonify({"error": True, "message": str(err)}), 403
                        elif err.source == Source.MANIFEST:
                            report.create_report(True, absolute_path, "Applying ressource is denied with the following warning : " + str(err))

                    except ApplyError as err:
                        logging.warning("%s" % str(err))
                        report.create_report(True, absolute_path, str(err))

        return jsonify(report.to_json()), 202
    else:
        return jsonify({"error": True, "message": "Folder name or config.json is missing"}), 403


def templatize_yaml(absolute_path, function_uid, message, request_params_to_complete, topic):
    """
    We use the Chevon lib to templatize the YAML that will be deployed to the cluster. The 4 variables bellow
    are always availble to be templatized. If the user doesn't set a variable ( {{var}} ) inside the YAML then it is not
    templatized
    :param absolute_path: The path to the YAML file to templatize
    :param function_uid: The function UID that corresponds to the unique run of the lambda
    :param message: The message or "payload" to give the lambda. It will generally be available inside the ENV section
    :param request_params_to_complete: The variables to templatize
    :param topic: The topic on wich the lambda has been called. This is mostly for information purpose
    :return: The templated version of the YAML file
    """
    b64_msg = base64.b64encode(bytes(message, 'utf-8'))
    request_params_to_complete["PAYLOAD"] = b64_msg.decode("utf-8")
    request_params_to_complete["FUNCTION_UID"] = function_uid
    request_params_to_complete["RANDOM"] = str(uuid.uuid4())
    request_params_to_complete["TOPIC"] = topic
    logging.debug("Object given to engine during templating of yaml to apply : %s" % str(request_params_to_complete))
    with open(absolute_path, 'r') as f:
        return chevron.render(f, request_params_to_complete)


logging.info("Running Apply version : %s" % os.environ.get("VERSION", "?"))

# INIT REDIS CONNECTION
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
if REDIS_PASSWORD is None:
    logging.fatal("Redis password is not set. Exiting now...")
    sys.exit(1)
r = redis.Redis(host='gitfaas-redis-master', port=6379, db=0, password=REDIS_PASSWORD)
wait_for_redis()

# INIT REDIS MINIMAL POPULATION
r.set("master_error", "False")
r.set("last_master_error_description", "")

# Checking redis data expiration value


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
