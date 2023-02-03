class LanguagesExamples:

    @staticmethod
    def python_starter():
        starter = """
#####################################
import base64
import os
import requests


def do_something(message):
    print(message)


def main():
    message = None

    # Retrieving the base64 payload (the input message sent to this function)
    b64_message = os.environ.get('PAYLOAD', None)

    if b64_message is not None:
        # Decoding base64 payload into usable string
        message = base64.b64decode(b64_message).decode("utf-8")
    
    # Retrieving the function UID (UID that identifies the current run of this function)
    function_uid = os.environ.get('FUNCTION_UID', None)

    do_something(message)

    # Returning a response to Gitfaas
    url = "http://gitfaas:5000/response/" + function_uid  # We append the function_UID so that Gitfaas knows who is talking to it.

    # We send a string back to Gitfaas
    requests.post(url, data="hello world", headers={'Content-type': 'text/plain'})

main()
#####################################
        """
        print(starter)
        return starter

    @staticmethod
    def nodejs_starter():
        starter = """
/************************************/
const https = require('https');
const axios = require('axios');

function doSomething(message) {
    console.log(message)
}

function main() {
    message = null

    // Retrieving the base64 payload (the input message sent to this function)
    b64Payload = process.env.PAYLOAD
    if (typeof(b64Payload) !== "undefined")
        // Decoding base64 payload into usable string
        message = Buffer.from(b64Payload, 'base64').toString('utf-8');

    // Retrieving the function UID (UID that identifies the current run of this function)
    functionUid = process.env.FUNCTION_UID

    doSomething(message)

    // We send data back to Gitfaas
    const bodyParameters = {
        hello: "world"
    };

    // Returning a response to Gitfaas ;  We append the function_UID so that Gitfaas knows who is talking to it.
    axios.post(
        "http://gitfaas.gitfaas.svc.cluster.local:5000/response/" + functionUid,
        bodyParameters,
        {headers: { 'Content-type': 'application/json' }}
    ).then(console.log).catch(console.log);
}

main()
/************************************/
        """
        print(starter)
        return starter
