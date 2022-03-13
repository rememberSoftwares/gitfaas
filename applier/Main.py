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
from functools import wraps

from Apply import Kubernetes

app = Flask(__name__)

WORK_PATH = os.environ.get("WORK_PATH", None)

current_config = None
folder_name = None
git_pid = None
g_error = False


def ready_to_use():
    return current_config is not None and folder_name is not None


@app.route('/alive', methods=["GET"])
def alive():
    return jsonify({"alive": True})


@app.route('/folderName', methods=["POST"])
def update_folder_name():
    global folder_name
    folder_name = request.json["folderName"]
    return jsonify({"error": False})

@app.route('/pidUpdate', methods=["POST"])
def update_pid():
    global git_pid
    git_pid = int(request.json["pid"])
    return jsonify({"error": False})


@app.route('/configUpdate', methods=["POST"])
def update_config():
    global current_config
    global g_error
    try:
        current_config = json.loads(request.json)
        g_error = False
    except Exception as e:
        g_error = True
        logging.error(traceback.format_exc())
        return {"error": True, "message": "Loading config.json failed. Check common JSON issues like missing comas etc"}
    return jsonify({"error": False})

@app.route('/refresh', methods=["GET"])
def refresh():
    if git_pid is None:
        return jsonify({"error": True, "message": "Pid of GIT container unknown. This should have been auto configured on startup"})
    os.kill(git_pid, signal.SIGUSR1)
    return jsonify({"error": False})


@app.route('/publish/<topic>', methods=["POST"])
def publish(topic):
    if g_error is True:
        return jsonify({"error": True, "message": "App state is in ERROR. No requests will be served until resolution !"})
    report = []
    if request.content_type.startswith('application/json'):
        message_text = json.dumps(request.json)
    elif request.content_type.startswith('text/plain'):
        message_text = str(request.data)
    else:
        return jsonify({"error": True, "message": "No contentType detected. Please use application/json or text/plain."})

    if ready_to_use():
        for current_topic in current_config["topics"]:
            if current_topic["name"] == topic:
                for file_path in current_topic["configs"]:
                    absolute_path = WORK_PATH + "/" + folder_name + "/" + file_path
                    template_params = request.args.to_dict()# if len(request.args) <= 0 or request.args is None else {}
                    try:
                        yaml_to_apply = set_labels(absolute_path, "UUID_@todo", message_text, template_params)
                    except FileNotFoundError:
                        print("[WARN]: File to apply not found. Check config.json !")
                        report.append({"error": True, "path": absolute_path})
                        continue
                    Kubernetes.apply_from_stdin(yaml_to_apply)
                    report.append({"error": False, "path": absolute_path})
        return jsonify(report)
    else:
        return jsonify({"error": True, "message": "Folder name or config.json is missing"})


def set_labels(absolute_path, request_uuid, message, template_params):
    b64_msg = base64.b64encode(bytes(message, 'utf-8'))
    template_params["MESSAGE"] = b64_msg.decode("utf-8")
    template_params["REQUEST_UUID"] = request_uuid
    template_params["RANDOM"] = str(uuid.uuid4())
    with open(absolute_path, 'r') as f:
        return chevron.render(f, template_params)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
