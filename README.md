<p align="center"><img src="https://user-images.githubusercontent.com/6358314/177987795-0b817149-14f0-45c2-8d50-d22df8629c20.png" width="500"></p>
<p align="center"><b>Easily deploy FAAS lambdas or any ressources on Kubernetes using GitOps and REST API</b></p>

<hr>

# gitfaas

A framework for serverless functions on Kubernetes.  
Gitfaas can apply any Kubernetes manifest using its REST API. It emphases on providing long running Kubernetes jobs and gives you full control over the manifest content.  


Write short-lived functions in any language, and map them to HTTP requests (or other event triggers).

Deploy functions instantly with one command. There are no containers to build, and no Docker registries to manage.
A mix between GitOps and FAAS to create data pipelines on Kubernetes

Gitfaas allows you to apply Kubernetes manifests by making HTTP requests. Even though it can apply anything it focuses on making pipelines of long running jobs that can start other jobs themselves. It's the perfect match to create data pipelines (Collect, uncompress, convert data, etc.).

Gitfaas acts like a [GitOps](https://www.weave.works/technologies/gitops/) technology would ([Weave](https://github.com/weaveworks/weave-gitops), [Argo](https://argo-cd.readthedocs.io/en/stable/)) by pulling a git repository. Any updates made to this repository will get reflected as Gitfaas will try to pull frequently to always be up-to-date.

Gitfaas is a FAAS (Function As A Service) like [Openfaas](https://www.openfaas.com/) or [Fission](https://fission.io/) meaning that it provides developers with serverless containers.

Project status : BETA STABLE  
If you have any errors please create an issue. Thx  

## Functionalities

* **One pod per request** : Each of your requests to Gitfaas will be served by a new pod. This tends to create longer responses in time but allows dealing with volumes far easily.
* **Volumes** : Each new pod created can have its own fresh volume by creating PVCs on the fly. When the pod is deleted, so is the PVC.
* **Scale to 0** : When no function is invoked, no pod is created. One request makes one pod and one optional volume. When finished the pod and the volume are both deleted. This way you don't have to pay for unused resources.
* **Retry** : When your serverless function need to restart you can trigger the recreation of the pod.
* **Topics** : Trigger functions using topics (the same way as you would using NATS/RabbitMQ). A function can listen to multiple topics.
* **Responses** : Your lambdas can post the result independant of the time they take. No timeouts to configure. All results are stored and can be viewed at any time. 
* **Industry standards security** : Using RBAC, minimal images, preventing configuration injection.
* **Integration with any languages** : You don't have to update your codebase (only needs access to ENV and a network lib).
* **Apply whatever you want** : Gitfaas was meant to apply lambdas but you can give it any YAML manifest to apply.

## Installation

Cloning this repository :  
```
git clone https://github.com/rememberSoftwares/gitfaas.git
cd gitfaas\
```
Install using Helm : 
You need at least a Git server URL, a username and a way to clone the repo. Here we use a personnal token token but you can edit the `helm_chart/values.yaml` to activate SSH keys instead.  
```
helm install gitfaas . -n gitfaas --create-namespace --set app.git.url="<YOUR_REPO_URL>" --set app.git.userName="<A_GIT_USERNAME>" --set app.git.http.personalToken="A_GIT_PERSONNAL_TOKEN"
```
More information on the git personal token : [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)  

Need help installing ? Follow this in depth tutorial.

## Helm chart most common configuration

| Parameter | Description | Default |
| --- | --- | --- |
| `rbac.scope` | Scope of Kubernetes RBAC. Can either be "clusterWide" or "namespaced". In "namespace mode", gitfaas can only apply ressources inside its own namespace. This is recommended for security reasons. When choosing "clusterWide" mode, gitfaas can apply manifest within any namespaced not only his own. | `namespaced` |
| `app.git.url` | URL of your Git repo. This might be Github, Gitlab or any GIT compatible server. Gitfaas uses GitOps principles so all of your lambdas and manifests are stored in git | `<MUST_BE_SET>` |
| `app.git.username` | The Git username to be used when cloning/pulling- the Repo | `<MUST_BE_SET>` |
| `app.git.pullBranch` | The Git branch that will be pulled. Github when from "master" to "main" so we will also reflect the change here. | `main` |
| `app.git.pollingInterval` | How often (in minutes) the repo will be pulled. This can be decreased for dev env and increased for production. No need to spam. | `10` |
| `app.git.logLevel` | Application will write logs that can be viewed using kubectl logs. Availble levels are "INFO", "DEBUG" and "WARN" | `INFO` |
| `app.git.http` | You can either use HTTP or SSH to give gitfaas clone capability. If you wish to go with a personnal token you can get one from your Git provider. Check out this documentation @todo link to get information on how to get the token. | (none) |
| `app.git.sshKey.usePrivateKey` | You can either use HTTP or SSH to give gitfaas clone capability. If you wish to use SSH then you must provide Gitfaas with a valid SSH private key. Check out this documentation @todo link if you need help setting things up. Availble values are "yes" or "no". Setting this to "yes" will override the use of the personnal token even if it is set. Also you must configure the parameters that follows. | `no` |
| `app.git.sshKey.privKeySecretName` | Name of the Kubernetes secret containing the private ssh key allowing to clone the Git repository. The file name inside the secret MUST BE "id_rsa". Command to generate secret is available as a comment inside the values.yaml. It should be deployed in the same namespace as Gitfaas.  | `gitfaas-ssh-key` |
| `app.git.sshKey.knowHostMultiLine` | To prevent MIM attacks this should be set to valid know host. This ensure that gitfaas is contacting your Git server and not a fake one. To generate thoses report to this documentation help @todo link. You can also deactivate the key check with the next parameters but it is NOT recommanded. You can also use HTTP auth with personnal token wich doesn't need this at all. | (none) |
| `app.git.sshKey.strictHostKeyChecking` | Available values are "yes" or "no". If set to "no" then key checking when using ssh key authentification will be deactivated. This is not recommanded as someone might try MIM attacks. Prefer using personnal token authentication instead. | `yes` |
| `app.apply.bannedKubeRessources` | This is a list of separated (by space) Kubernetes ressources that really shouldn't be allowed to be applied by gitfaas. Allowing someone to apply thoses might give an attacker the posibility to give him acccess to your cluster and compromise gitfaas. This list should be extended if needed. Remember that Gitfaas is protected by RBAC and can only deploy "pods", "services", "deployments" and "jobs". To apply other kinds of ressource you will need to update this rbac with you own RBAC Role and RoleBinding. Check this documentation to update gitfaas RBAC @todo link.  | `Role RoleBinding ClusterRole ClusterRoleBinding ServiceAccount Ingress` |
| `app.apply.logLevel` | Application will write logs that can be viewed using kubectl logs. Availble levels are "INFO", "DEBUG" and "WARN" | `INFO` |
| `app.apply.configurationPath` | Gitfaas uses a single JSON configuration file to define topics and lambdas. This file must be present inside the Github repository. This setting will overwrite the default location wich is at the root of the repo. Full path from root is mandatory but do not start with "/". ie "folder_1/folder_2/my_topic_settings.json" | `config.json` |
| `redis.auth.password` | Redis password. Redis is used by gitfaas to store lambdas responses and other run time information. It is best to be updated with something random. | `redacted` |

## Basic configuration

How to configure Gitfaas to start a function ?  
It's quite easy. You just have to create a config.json at the root of your git repository.  

_"Inside your git repository"_  
Create a file `config.json` and follow this simple JSON structure  
```
{
    "topics":[
        {
            "name": "<NAME_OF_THE_TOPIC>",
            "configs": [
                "<NAME_OF_KUBE_MANIFEST_INSIDE_THIS_REPO>.yaml"
            ]
        }
    ]
}
```
Take a look at the above configuration. It's all about defining a topic name and a list of files to apply when this topic is triggered.  

Let's make a real example :  
```
{
    "topics":[
        {
            "name": "timeToCollect",
            "configs": [
                "collect.yaml"
            ]
        },
        {
            "name": "timeToUncompress",
            "configs": [
                "uncompress.yaml"
            ]
        }
    ]
}
```
In the above configuration we have instructed Gitfaas to apply the file `collect.yaml` when it receives a message on the `timeToCollect` topic.  
The file collect.yaml will be applied on the cluster. This file can be anything you want. But if you need to make pipelines with scale to 0 and volumes you'll have to respect the correct kind of Kubernetes manifest. Continue this lecture to know more.  


## Basic function deployment

Even though Gitfaas can apply anything, if you want all the functionalities advertised you need to use the following Kubernetes manifest:
```
apiVersion: batch/v1
kind: Job
metadata:
  name: some-pod-name-{{RANDOM}}
  namespace: <REPLACE_NAMESPACE>
spec:
  template:
    spec:
      containers:
      - name: myfunction
        image: <REPLACE_YOUR_IMAGE>
        command: ["python3", "handler.py"]
        env:
        - name: MESSAGE
          value: "{{MESSAGE}}"
        - name: REQUEST_UUID
          value: "{{REQUEST_UUID}}"
      restartPolicy: Never
````
The above configuration in the minimal deployment.  
**DO NOT EDIT ALL THE `{{...}}` as it is part of Gitfaas.**  

The interesting part is :  
```
        env:
        - name: MESSAGE
          value: "{{MESSAGE}}"
        - name: REQUEST_UUID
          value: "{{REQUEST_UUID}}"
```

This is how your function gets the message that has been posted on the topic.  
In your code simply extract the message from the ENV. Please note that it will be encoded using base64. This is useful to ensure the message is not corrupted (like double quotes to simple quotes when using JSON payloads).  
In python this is how your function would extract the message :
```
def main():
    b64_message = os.environ.get('MESSAGE', None)
    if b64_message is None:
        print("No message in env")
        return
    message = base64.b64decode(b64_message)
    message = message.decode("utf-8")
    print("message = ", message)
    # have fun
```

# How to scale to 0

Scaling to 0 allows you to manage the cost of your infrastructure.  
This functionality is achieved using a Kubernetes key called `ttlSecondsAfterFinished`.  
Take the default job deployment and add this new key to it:  
```
apiVersion: batch/v1
kind: Job
metadata:
  name: some-pod-name-{{RANDOM}}
  namespace: <REPLACE_NAMESPACE>
spec:
  ttlSecondsAfterFinished: 60  # <= The magic comme from here
  template:
    spec:
      containers:
      - name: myfunction
        image: <REPLACE_YOUR_IMAGE>
        command: ["python3", "handler.py"]
        env:
        - name: MESSAGE
          value: "{{MESSAGE}}"
        - name: REQUEST_UUID
          value: "{{REQUEST_UUID}}"
      restartPolicy: Never
```

Setting `ttlSecondsAfterFinished: <NUMBER_IN_SECONDS>` allows Kubernetes to destroy the Job itself when it is finished.  
When the job is removed, so is the pod created. 60 seconds is a good value but if you need to check the logs then use a bigger value.  

## Retrying

This can be done using `backoffLimit: <MAX_NUMBER_OF_RETRIES>`
```
apiVersion: batch/v1
kind: Job
metadata:
  name: some-pod-name-{{RANDOM}}
  namespace: <REPLACE_NAMESPACE>
spec:
    backoffLimit: 1  # <= The magic comme from here
  template:
    spec:
      containers:
      - name: myfunction
        image: <REPLACE_YOUR_IMAGE>
        command: ["python3", "handler.py"]
        env:
        - name: MESSAGE
          value: "{{MESSAGE}}"
        - name: REQUEST_UUID
          value: "{{REQUEST_UUID}}"
      restartPolicy: Never
```

@todo : This needs more information on how to trigger. TL;DR return anything else than 0 inside your container and it should trigger retry.

## Using volumes

Serverless functions should be able to use volumes. The function stays stateless as when the function exits the volume is also deleted.

```
apiVersion: batch/v1
kind: Job
metadata:
  name: some-pod-name-{{RANDOM}}
  namespace: <REPLACE_NAMESPACE>
spec:
  backoffLimit: 0
  template:
    spec:
      containers:
      - name: myfunction
        image: <REPLACE_IMAGE>
        command: ["python3", "handler.py"]
        env:
        - name: MESSAGE
          value: "{{MESSAGE}}"
        - name: REQUEST_UUID
          value: "{{REQUEST_UUID}}"
        volumeMounts:
          - name: my-light-volume
            mountPath: /mnt/disk/
      restartPolicy: Never
      volumes:
        - name: my-light-volume
          ephemeral:
            volumeClaimTemplate:
              metadata:
                labels:
                  type: my-volume
              spec:
                accessModes: [ "ReadWriteOnce" ]
                storageClassName: "csi-cinder-high-speed"  # <= You might need to update this
                resources:
                  requests:
                    storage: 1Gi  # <= set the size of your volume here
```

This creates a scratch volumes inside the pod. If you look for PVCs you will see that a PVC is created with a random name in the same namespace.  
When the pod is deleted/finished the PVC is also deleted automatically.


## Complete example

```
apiVersion: batch/v1
kind: Job
metadata:
  name: some_pod-name-{{RANDOM}}
  namespace: <REPLACE_NAMESPACE>
spec:
  ttlSecondsAfterFinished: 60
  backoffLimit: 0
  template:
    spec:
      containers:
      - name: myfunction
        image: <REPLACE_IMAGE>
        command: ["python3", "handler.py"]
        env:
        - name: MESSAGE
          value: "{{MESSAGE}}"
        - name: REQUEST_UUID
          value: "{{REQUEST_UUID}}"
        volumeMounts:
          - name: my-light-volume
            mountPath: /mnt/disk/
          - name: my-projected-secrets
            mountPath: /var/somefolder/secrets
      restartPolicy: Never
      volumes:
        - name: my-projected-secrets
          projected:
            defaultMode: 420
            sources:
            - secret:
                items:
                - key: secret-name
                  path: secret-name
                name: secret-name
        - name: my-light-volume
          ephemeral:
            volumeClaimTemplate:
              metadata:
                labels:
                  type: my-volume
              spec:
                accessModes: [ "ReadWriteOnce" ]
                storageClassName: "csi-cinder-high-speed"
                resources:
                  requests:
                    storage: 1Gi
```

* This example will create a pod that will scale to zero 60 seconds after being finished.
* It has a fresh volume of 1 GO mounted to `/mnt/disk`.
* It has a secret (must exist in the namespace) mounted as file in `/var/somefolder/secrets`
* Retry is deactivated (set to 0) so if the job fails it won't reboot.


## Launching a function via the REST API

To start a job use the following routes:

* POST _http://gitfaas:5000/publish<TOPIC>_
* Data : Some JSON / text
* Header : Content type can either be application/json or plain/text

With curl :
```
 curl "http://gitfaas:5000/publish/mytopic" -X POST -d '{ "hello": "world" }' -H 'Content-Type: application/json'
```
This will apply all Kubernetes manifests listening on the topic _"mytopic"_.

Note that you can use query params to template anything in the manifest.  
For instance, edit the YAML of the manifest :  
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: some-pod-name-{{RANDOM}}
spec:
  replicas: {{replicas}}
...
```

Now publish a message using this query params : `http://gitfaas:5000/publish/mytopic&replicas=2`  

This will be rendered and then apply like this :  
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: some-pod-name-{{RANDOM}}
spec:
  replicas: 2
...
```

---

To refresh the GIT repository inside Gitfaas without having to wait the automatic sync use :  
* GET _http://gitfaas:5000/refresh_

With curl :
```
 curl "http://gitfaas:5000/refresh" -H 'Content-Type: application/json'
```
