import time
import requests
import os
import base64
import json

def main():

    # Retrieving the base64 payload (the input message sent to this function) 
    b64_message = os.environ.get('PAYLOAD', None)
    # Retrieving the function UID (UID that identifies the current run of this function and allows to distinct multiple runs of the same function)
    function_uid = os.environ.get('FUNCTION_UID', None)

    if b64_message is None:
        print("No message in env")
        return

    # Decoding base64 JSON payload into usable JSON
    str_message = base64.b64decode(b64_message).decode("utf-8")
    json_message = json.loads(str_message)

    # Waiting for the indicated period of time (given inside the payload)
    print("waiting for %s" % json_message["sleep_time"])
    time.sleep(int(json_message["sleep_time"]))


    # Returning a response to Gitfaas
    url = "http://gitfaas:5000/response/" + function_uid
    print("Responding on = %s" % url)
    try:
        print("Reversed string as response : %s" % json_message["some_string"][::-1])

        # The response contains a reversed version of the string present inside the payload
        ret = requests.post(url, json={"reversed_value": json_message["some_string"][::-1]})
        print("Response return = %s" % ret)

    except Exception as e:
        print("Error responding : %s" % str(e))


main()
