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


@app.route('/publish/<topic>', methods=["POST"])
def publish(topic):
    if r.get("error").decode("utf-8") == "True":
        return jsonify({"error": True, "message": "App state is in ERROR. No requests will be served until resolution !"})
    if topic == "":
        return jsonify(
            {"error": True, "message": "Topic cannot be an empty string"})
    report = []
    print("[INFO]: Topic [" + topic + "]")
    print("topic = ", topic, file=sys.stderr)
    print("Folder name = ", r.get("folder_name"), file=sys.stderr)
    print("current config = ", r.get("current_config"), file=sys.stderr)
    print("please show this = ", str(request.args), file=sys.stderr)
    if request.content_type.startswith('application/json'):
        print("JSON ! ", file=sys.stderr)
        print("plop ", str(request.json), file=sys.stderr)
        message_text = json.dumps(request.json)
    elif request.content_type.startswith('text/plain'):
        print("text ! ", file=sys.stderr)
        print("plop ", request.data, file=sys.stderr)
        message_text = str(request.data)
    else:
        return jsonify({"error": True, "message": "No contentType detected. Please use application/json or text/plain."})

    if ready_to_use():
        current_config = json.loads(r.get("current_config"))
        for current_topic in current_config["topics"]:
            if current_topic["name"] == topic:
                for file_path in current_topic["configs"]:
                    absolute_path = WORK_PATH + "/" + r.get("folder_name").decode("utf-8") + "/" + file_path
                    template_params = request.args.to_dict()# if len(request.args) <= 0 or request.args is None else {}
                    print("template params = ", str(template_params), file=sys.stderr)
                    print(str(type(template_params)), file=sys.stderr)
                    try:
                        yaml_to_apply = templatize_yaml(absolute_path, "UUID_@todo", message_text, template_params, topic)
                    except FileNotFoundError:
                        print("[WARN]: File to apply not found. Check config.json !")
                        report.append({"error": True, "path": absolute_path})
                        continue
                    print("yaml stuff = ", yaml_to_apply, file=sys.stderr)
                    Kubernetes.apply_from_stdin(yaml_to_apply)
                    report.append({"error": False, "path": absolute_path})
        return jsonify(report)
    else:
        return jsonify({"error": True, "message": "Folder name or config.json is missing"})


def templatize_yaml(absolute_path, request_uuid, message, template_params, topic):
    b64_msg = base64.b64encode(bytes(message, 'utf-8'))
    template_params["MESSAGE"] = b64_msg.decode("utf-8")
    template_params["REQUEST_UUID"] = request_uuid
    template_params["RANDOM"] = str(uuid.uuid4())
    template_params["TOPIC"] = topic
    print("final = ", template_params, file=sys.stderr)
    with open(absolute_path, 'r') as f:
        return chevron.render(f, template_params)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
