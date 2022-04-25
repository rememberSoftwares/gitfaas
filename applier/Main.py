import signal

from flask import Flask, render_template, jsonify, request
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

from Apply import Kubernetes

app = Flask(__name__)

WORK_PATH = os.environ.get("WORK_PATH", None)

#current_config = None
#folder_name = None
#git_pid = None
#g_error = False
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)
if REDIS_PASSWORD is None:
    print("Redis password is not set. Exiting now..")
    sys.exit(1)
r = redis.Redis(host='gitfaas-redis-master', port=6379, db=0, password=REDIS_PASSWORD) #temp test password

r.set('error', "False")


def ready_to_use():
    return r.get("current_config") is not None and r.get("folder_name") is not None and r.get("error").decode("utf-8") == "False"


@app.route('/alive', methods=["GET"])
def alive():
    return jsonify({"alive": True})


@app.route('/folderName', methods=["POST"])
def update_folder_name():
    #global folder_name
    r.set("folder_name", request.json["folderName"])
    #folder_name = request.json["folderName"]
    return jsonify({"error": False})

@app.route('/pidUpdate', methods=["POST"])
def update_pid():
    r.set("git_pid", int(request.json["pid"]))
    return jsonify({"error": False})


@app.route('/configUpdate', methods=["POST"])
def update_config():
    try:
        json.loads(request.json)
        r.set("current_config", request.json)
        r.set("error", "False")
    except Exception as e:
        r.set("error", "True")
        logging.error(traceback.format_exc())
        return {"error": True, "message": "Loading config.json failed. Check common JSON issues like missing comas etc"}
    return jsonify({"error": False})

@app.route('/refresh', methods=["GET"])
def refresh():
    git_pid = r.get("git_pid")
    if git_pid is None:
        return jsonify({"error": True, "message": "Pid of GIT container unknown. This should have been auto configured on startup"})
    os.kill(int(git_pid), signal.SIGUSR1)
    return jsonify({"error": False})

"""
Stores inside redis the answer of a faas function.
function_uid's key in redis is init by publish() : If the user gives an unknown uid then the value from redis will be None and the
request will be denied.
"""
@app.route('/answer/<function_uid>', methods=["POST"])
def post_answer(function_uid):
    if len(function_uid) != 77 or re.match(r"f\-\w+\-\w+\-\w+\-\w+\-\w+\-r-\w+-\w+-\w+-\w+-\w+", function_uid) is False or r.get(function_uid) is None:
        return jsonify({"error": True, "message": "Function uid is invalid. Are you sure you want to GET this ressource and not POST a new one ?"})
    if request.content_type is None:
        return jsonify(
            {"error": True, "message": "No contentType detected. Please use application/json or text/plain."})
    elif request.content_type.startswith('application/json'):
        message_text = json.dumps(request.json)
    elif request.content_type.startswith('text/plain'):
        message_text = request.data.decode("utf-8")
    else:
        return jsonify(
            {"error": True, "message": "No contentType detected. Please use application/json or text/plain."})
    if message_text is None or message_text == "":
        return jsonify({"error": True, "message": "Data field in POST request cannot be empty."})
    b64_msg = base64.b64encode(bytes(message_text, 'utf-8'))
    r.set(function_uid, b64_msg)
    return jsonify({"error": False, "message": "Answer stored correctly"})

@app.route('/answer/<request_uid>', methods=["GET"])
def get_answer(request_uid):
    if len(request_uid) != 38 or re.match(r"r-\w+-\w+-\w+-\w+-\w+", request_uid) is False:
        print("BAM error", file=sys.stderr)
        return jsonify({"error": True, "message": "Function uid is invalid", "answers": []})
    function_uids = r.get(request_uid)
    if function_uids is None:
        return jsonify({"error": False, "answers": []})
    function_uids_list = function_uids.decode("utf-8").split("|")
    answers_aggregation = []
    for function_uid in function_uids_list:
        print("function uid = " + str(function_uid), file=sys.stderr)
        function_answer = r.get(function_uid)
        answers_aggregation.append(None if (function_answer is None or function_answer.decode("utf-8") == "") else function_answer.decode("utf-8"))
    return jsonify({"error": False, "answers": answers_aggregation})

@app.route('/publish/<topic>', methods=["POST"])
def publish(topic):
    if r.get("error").decode("utf-8") == "True":
        return jsonify({"error": True, "message": "App state is in ERROR. No requests will be served until resolution !"})
    if topic == "":
        return jsonify(
            {"error": True, "message": "Topic cannot be an empty string"})
    report = {"requestUid": None, "applies": [], "error": False}
    print("[INFO]: Topic [" + topic + "]", file=sys.stderr)
    print("topic = ", topic, r.get("folder_name"), file=sys.stderr)
    if request.content_type is None:
        return jsonify(
            {"error": True, "message": "No contentType detected. Please use application/json or text/plain."})
    elif request.content_type.startswith('application/json'):
        message_text = json.dumps(request.json)
    elif request.content_type.startswith('text/plain'):
        message_text = str(request.data)
    else:
        return jsonify({"error": True, "message": "No contentType detected. Please use application/json or text/plain."})

    if ready_to_use():
        current_config = json.loads(r.get("current_config"))
        request_uid = "r-" + str(uuid.uuid4())
        r.set(request_uid, "")
        report["requestUid"] = request_uid
        for current_topic in current_config["topics"]:
            if current_topic["name"] == topic:
                for file_path in current_topic["configs"]:
                    absolute_path = WORK_PATH + "/" + r.get("folder_name").decode("utf-8") + "/" + file_path
                    template_params = request.args.to_dict()# if len(request.args) <= 0 or request.args is None else {}
                    function_uid = add_function_uid_to_request(request_uid)
                    try:
                        yaml_to_apply = templatize_yaml(absolute_path, function_uid, message_text, template_params, topic)
                    except FileNotFoundError:
                        print("[WARN]: File to apply not found. Check config.json !")
                        report["applies"].append({"error": True, "path": absolute_path})
                        report["error"] = True
                        continue
                    Kubernetes.apply_from_stdin(yaml_to_apply)
                    report["applies"].append({"error": False, "path": absolute_path})
        return jsonify(report)
    else:
        return jsonify({"error": True, "message": "Folder name or config.json is missing"})

"""
Array of functions uid are stored like : "uid1|uid2|uid2"
Each uid is the concatenation of the request uid + the function uid. This allows to retrieve the request uid from
the function uid. The key and values for example : <r-xxxx>:f-yyyy-r-xxxx|f-zzzz-r-xxxx
A simple uid is made of 36 char + 2 char for identification (r- for request uids and f- for function uids).
In the end the request uid is made of 38 chars and each function uid is made of 2 * 38 chars + a dash separating them both
=> 77 chars
"""
def add_function_uid_to_request(request_uid):
    current_list_content = r.get(request_uid).decode("utf-8")
    function_uid = "f-" + str(uuid.uuid4()) + "-" + request_uid
    # We init the function_uid in redis to allow POST /anwser to update this key. POST /answer cannot store anything in a
    # key that isn't initialized (for security reasons)
    r.set(function_uid, "")
    if current_list_content is None or current_list_content == "":
        r.set(request_uid, function_uid)
    else:
        r.set(request_uid, current_list_content + "|" + function_uid)
    return function_uid


def templatize_yaml(absolute_path, function_uid, message, template_params, topic):
    b64_msg = base64.b64encode(bytes(message, 'utf-8'))
    template_params["MESSAGE"] = b64_msg.decode("utf-8")
    template_params["FUNCTION_UID"] = function_uid
    template_params["RANDOM"] = str(uuid.uuid4())
    template_params["TOPIC"] = topic
    print("final = ", template_params, file=sys.stderr)
    with open(absolute_path, 'r') as f:
        return chevron.render(f, template_params)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
