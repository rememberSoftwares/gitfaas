# gitfaas
A mix between GitOps and FAAS to create data pipelines on Kubernetes

Gitfaas allows you to apply Kubernetes manifests by making HTTP requests. Even though it can apply anything it focuses on making pipelines of long running jobs that can start other jobs themselves. It's the perfect match to create data pipelines (Collect, uncompress, convert data, etc.).

Gitfaas acts like a [GitOps](https://www.weave.works/technologies/gitops/) technology would ([Weave](https://github.com/weaveworks/weave-gitops), [Argo](https://argo-cd.readthedocs.io/en/stable/)) by pulling a git repository. Any updates made to this repository will get reflected as Gitfaas will try to pull frequently to always be up-to-date.

Gitfaas is a FAAS (Function As A Service) like [Openfaas](https://www.openfaas.com/) or [Fission](https://fission.io/) meaning that it provides developers with serverless containers.

project status : PRE-ALPHA  
Do not use in production before BETA. Everything works but is you try to break it, it will break.  

## Functionalities

* **One pod per request** : Each of your requests to Gitfaas will be served by a new pod. This tends to create longer responses in time but allows dealing with volumes far easily.
* **Volumes** : Each new pod created can have its own fresh volume by creating PVCs on the fly. When the pod is deleted, so is the PVC.
* **Scale to 0** : When no function is invoked, no pod is created. One request makes one pod and one optional volume. When finished the pod and the volume are both deleted. This way you don't have to pay for unused resources.
* **Retry** : When your serverless function need to restart you can trigger the recreation of the pod.
* **Topics** : Trigger functions using topics (the same way as you would using NATS/RabbitMQ). A function can listen to multiple topics.

## Installation

Gitfaas uses a kube config file to interact with the API-server. For now, we must start by creating a secret containing this configuration. In future updates we'll need to find a better way.  
Remember that you can control the kube config permissions by using service accounts and RBAC.  

In this example we will use the kube config present in your ~/.kube on your filesystem, assuming that your machine has access to the targeted Kubernetes cluster.  

```
 kubectl create secret generic kubeconfig  --from-file=~/.kube/config -n <REPLACE_NAMESPACE> -o yaml --dry-run=client > secret.yaml
 kubectl apply -f secret.yaml
```
In the above replace <REPLACE_NAMESPACE> with the targeted namespace.  

Now let's configure and install Gitfaas.   
```
git clone https://github.com/rememberSoftwares/gitfaas.git
cd gitfaas
```
Edit `deploy.yaml` and replace all `<REPLACE>` using the correct values.  

```
        env:
        - name: GIT_URL
          value: "<REPLACE>"    # <= Your private repository URL containing the configurations that can be apply by gitfaas
        - name: GIT_USER_NAME
          value: "<REPLACE>"    # <= A git username that can clone/pull the repository
        - name: GIT_PERSONAL_TOKEN
          value: "<REPLACE>"    # <= A personal token (revocable) acting as your password.
```
More information on the git personal token : [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

```
kubectl apply -f deploy.yaml -n <REPLACE_NAMESPACE>
```

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


## Starting a job

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
