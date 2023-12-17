This simple function (lambda) works like the .replace() function of python.  

It takes 3 arguments.  
* A source message to work on.
* A word that will be replaced
* A word to replace with

The expected JSON payload to give the function is the following

```
{
    "source": "I like bananas",
    "str-to-replace": "bananas",
    "replace-with": "apples"
}
```

The function will print and return the replaced string as a raw string, ie: "I like apples"


# Build
```
./buildAndPushDemo.sh 0.0.1
```

# Commit to Gitfaas

Commit the file `./replace_job.yaml` to the GIT repo setup with Gitfaas.  
Add the following configuration to your Gitfaas configuration file inside the repo :  
```
{
    "topics":[
        {
            "name": "replace",
            "configs": [
                "replace_job.yaml"
            ]
        }
    ]
}
```
If you already have a config file setup, simply mix the file by adding the new topic.  

# Deploy using API

Now that Gitfaas has the Job definition and a topic to listen to you can start the Job using a simple curl.

```
PAYLOAD=$(cat << EOF
{
  "source": "I like bananas",
  "str-to-replace": "bananas",
  "replace-with": "apples"
}
EOF
)
    
curl http://gitfaas/publish/replace -d "$(PAYLOAD)"
```
