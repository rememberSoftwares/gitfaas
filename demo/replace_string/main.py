import requests
import os
import base64
import json

# This function/lambda replaces a word inside a string. It takes 3 arguments.
# * A source message to work on.
# * A word that will be replaced
# * A word to replace with
#
# Ie: Expected payload format in input message
# {
#    "source": "I like bananas",
#    "str-to-replace": "bananas",
#    "replace-with": "apples"
# }

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

    # Creating a new string using python's .replace() method. We replace the term contained in "str-to-replace" with the one from "replace-with"
    replaced_string = json_message["source"].replace(json_message["str-to-replace"], json_message["replace-with"])
    print("Replaced string is : %s" % replaced_string)

    # Returning a response to Gitfaas
    url = "http://gitfaas:5000/response/" + function_uid # We append our function_UID so that Gitfaas knows who is talking to him.

    try:
        # We send a response to Gitfaas containing the replaced string. Setting content type to text/plain or application/json is a good practice.
        ret = requests.post(url, data=replaced_string, headers={'Content-type': 'text/plain'})
        print("Response return = %s" % ret.text)

    except Exception as e:
        print("Error responding : %s" % str(e))


main()
