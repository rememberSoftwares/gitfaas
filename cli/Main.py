import json
import pystache
import tempfile
import subprocess
import requests

from Question import *
from Starters import LanguagesExamples
from Config import PROMPT_VALUE



class RequestedValues:

    def __init__(self):
        self.function_name = "gitfaasfunction"

        self.must_scale_to_zero = False
        self.scale_to_zero_value = 0

        self.must_retry = True
        self.retries = 3

        self.must_have_volume = False
        self.volume_size = 1

        self.must_set_namespace = False
        self.namespace = "gitfaas"

        self.image = "<must-be-replaced>"

        self.filled_template = None

    def generate_manifest(self):
        with open("job_template.yaml", "r") as f:
            content = f.read()
        template = pystache.parse(content)
        context = {
            "scale_to_zero_value": self.scale_to_zero_value,
            "retries": self.retries,
            "show_volumes": self.must_have_volume,
            "function_name": self.function_name,
            "image": self.image,
            "namespace": self.namespace,
            "volume_size": self.volume_size,
            "RANDOM": "{{RANDOM}}",
            "PAYLOAD": "{{PAYLOAD}}",
            "FUNCTION_UID": "{{FUNCTION_UID}}"
        }
        self.filled_template = pystache.render(template, context)
        print("The generated YAML of the function is as follow :")
        print(self.filled_template)
        print("")
        return self.filled_template

    def write_manifest_to_file(self):
        question = Question()

        while True:
            filename = question.ask_str_question("Filename to write on disk ? [str/?]", False, "FILE_NAME")
            try:
                with open(filename, "x") as file:
                    file.write(self.filled_template)
                    print(f"Text written to {filename} successfully.")
                    break
            except FileExistsError:
                print(f"File {filename} already exists. Please enter a different file name.")


def trigger_function():
    question = Question()
    payload = None
    headers = None

    gitfaas_url = question.ask_str_question("What is Gitfaas URL ? [str/empty/?]\n(Leave blank for defaults : 127.0.0.1:5000)", True, "GITFAAS_URL")
    if gitfaas_url == "":
        gitfaas_url = "127.0.0.1:5000"
    gitfaas_url = "http://" + gitfaas_url.strip("http://").strip("https://")
    must_send_payload = question.ask_boolean_question("Is there a specific payload to send to the function ? [y/n/?]", "PAYLOAD_TO_SEND")
    if must_send_payload is True:
        text_file = tempfile.NamedTemporaryFile(delete=False)
        text_file_name = text_file.name
        text_file.write("Replace this with the payload to send to the function then save & exit".encode())
        text_file.close()
        subprocess.run(["nano", text_file_name])
        with open(text_file_name, "r") as f:
            payload = f.read()
        content_type_choice = question.ask_choice_question("Should this payload be interpreted as JSON [j] or pure text [t] ?", ['j', 't'], "CONTENT_TYPE")
        if content_type_choice == 'j':
            headers = {"content-type": "application/json"}
        else:
            headers = {"content-type": "application/text"}

    topic_name = question.ask_str_question("Topic name to trigger the function [str/?]", False, "TOPIC_NAME")

    print("\n#####################")
    print(f"Publishing event on {gitfaas_url + f'/publish/{topic_name}'}")
    try:
        x = requests.post(gitfaas_url + f"/publish/{topic_name}", data=payload, headers=headers)
        print(f"Gitfaas responded with status code {x.status_code}")
        resp = json.loads(x.text)
        if resp["error"] is True:
            print("Gitfaas sent back an error :-(")
            if "message" in resp:
                print(f"=> {resp['message']}")
        else:
            print(f"{len(resp['applies'])} { 'functions have' if len(resp['applies']) > 1 else 'function has' } been started")
            for apply_result in resp['applies']:
                print(f"File {apply_result['path']} has been applied to the Kubernetes cluster !")
    except Exception as err:
        print("An error occurred. Gitfaas seems unreachable.")
        print("The error is :")

        print(str(err))
    print("#####################")
    print("\n\n\n\n")
    input("Press enter to go back to main menu")


def get_function_response():
    pass

def create_new_function():
    values = RequestedValues()
    question = Question()

    values.function_name = question.ask_str_question("What is the function's name ? [str/?]", False, "FUNCTION_NAME")
    values.must_scale_to_zero = question.ask_boolean_question(f"Function should scale to 0 ? [y/n/?]\n(Defaults to {values.must_scale_to_zero})", "SCALE_TO_0")
    if values.must_scale_to_zero is True:
        values.scale_to_zero_value = question.ask_int_question(f"After how many seconds should the function self delete ? [int/?]\n(Defaults to {values.scale_to_zero_value})", "SCALE_TO_0_VALUE")
    values.must_retry = question.ask_boolean_question(f"Function should retry (restart) in case of error ? [y/n/?]\n(Defaults to {values.must_retry})", "MUST_RETRY")
    if values.must_retry is True:
        values.retries = question.ask_int_question(f"How many times the function should retry ? [int/?]\n(Defaults to {values.retries})", "RETRIES")
    values.must_have_volume = question.ask_boolean_question(f"Function should have a fresh volume ? [y/n/?]\n(Defaults to {values.must_have_volume})", "MUST_HAVE_VOLUME")
    if values.must_have_volume is True:
        values.volume_size = question.ask_int_question(f"What is the size of the volume in Gi ? [int/?]\n(Defaults to {values.volume_size})", "VOLUME_SIZE")
    values.must_set_namespace = question.ask_boolean_question(f"Set namespace ?[y/n/?]\n(Defaults to {values.must_set_namespace})", "MUST_HAVE_NAMESPACE")
    if values.must_set_namespace is True:
        values.namespace = question.ask_str_question(f"Namespace of the function ? [str/?]\n(Default to {values.namespace})", True, "NAMESPACE_NAME", default=values.namespace)
    values.image = question.ask_str_question("What is the image name to deploy ? [str/?]\n(No defaults. This is mandatory)", False, "IMAGE_NAME")

    values.generate_manifest()
    values.write_manifest_to_file()

    see_starter = question.ask_boolean_question("Do you wish to see a starter method in python or nodejs as an example ? [y/n/?]", "SHOW_STARTER")
    if see_starter is True:
        starter_type = question.ask_choice_question("Do you wish to see python [p] starter or nodeJS [n] starter ?", ["p", "n"], None)
        if starter_type == "p":
            LanguagesExamples.python_starter()
        elif starter_type == "n":
            LanguagesExamples.nodejs_starter()
    print("\n\n\n\n")
    input("Press enter to go back to main menu")


while True:
    print("""
  ,ad8888ba,   88              ad88                                     
 d8"'    `"8b  ""    ,d       d8"                                       
d8'                  88       88                                        
88             88  MM88MMM  MM88MMM  ,adPPYYba,  ,adPPYYba,  ,adPPYba,  
88      88888  88    88       88     ""     `Y8  ""     `Y8  I8[    ""  
Y8,        88  88    88       88     ,adPPPPP88  ,adPPPPP88   `"Y8ba,   
 Y8a.    .a88  88    88,      88     88,    ,88  88,    ,88  aa    ]8I  
  `"Y88888P"   88    "Y888    88     `"8bbdP"Y8  `"8bbdP"Y8  `"YbbdP"'  
    """)
    print("""
    Trigger function      [1]
    Get function response [2]
    Create new function   [3]
    
    Enter option [1/2/3] to continue
    """)
    answer = input(PROMPT_VALUE)
    if answer.isdigit() is not True:
        print("Please answer a numeric option : '1' or '2', etc")
    elif answer == "1":
        trigger_function()
    elif answer == "2":
        get_function_response()
    elif answer == "3":
        create_new_function()
    else:
        print("This option is not available. Please enter one of the above options : '1', '2', etc")
