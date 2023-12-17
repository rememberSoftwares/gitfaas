class Help:
    scale_to_0 = """
Scaling to 0 is the ability of a function to delete itself when finished. This allows for better ressource management as
it won't take any more ressources when the workload is finished. This functionality is rendered possible by Kubernetes
as the created ressource will be a job. Kubernetes has a specific key in the job manifest that allows self deletion after
a specific period of time. Note that all traces of this function will have disappear and no more logs will be available.
            """
    scale_to_0_value = """
This is a numeric value in seconds. For instance entering 7200 is a 2 hours timeout. When the function ends it will self
delete after 2 hours. Note that all traces of this function will have disappear.  
    """
    function_name = """
The function name will appear in the pod name in Kubernetes. Each lambda should have its own unique name.
    """
    must_retry = """
If the pod is in error the pod can be restarted a specific number of time. It the answer is no the backOffLimit will be
set to 0 and if the pod crashes it won't restart. This can be controlled programmatically by specifying a specific exit
code in your program.
    """
    retries = """
The number of time the pod it be restarted. If set to 1 the pod will be started once and if it crashes it will be
restarted. If it crashed again it won't be restarted anymore. Increasing this value will allow more restarts. 
    """
    must_have_volume = """
Pods can have volumes. If a volume is added it will be a new one. Each functions can mount a fresh volume at startup.
When the pod is deleted (by using scale to zero or manually deleted) then the volume will also delete itself.
    """
    volume_size = """
The size of the volume in Gi. The volume will be a fresh new one at each new function start.
    """
    must_have_namespace = """
By default, not setting the namespace will deploy the function in the Gitfaas namespace. Note that deploying in other
namespaces than the default one will be blocked if the RABC mode isn't defined as cluster wide (defaults to 'namespaced').
Check the helm chart to update this value if needed.
    """
    namespace_name = """
The name of the namespace in which the function will be deployed. Note that deploying in other namespaces than the default
one will be blocked if the RABC mode isn't defined as cluster wide (defaults to 'namespaced'). Check the helm chart to
update this value if needed.
    """
    image_name = """
The docker (or other container technology) image to be deployed by the Pod. If it's not on a public registry then it must
include the complete url to the repo. 
    """
    file_name = """
Now that the YAML manifest of the function has been generated it must be write to a file so that it be committed to a git
repo.
    """
    gitfaas_url = """
Gitfaas should be accessible inside the kubernetes cluster. The most common usecase is to port-forward the Gitfaas service
ie: kubectl port-forward -n gitfaas svc/gitfaas 5000:5000     
    """
    payload_to_send = """
The payload to send is a message that will be given to the triggered function. It will be available as $PAYLOAD in the
pod's env.
    """
    topic_name = """
The topic name is used to send a payload to the specific topic. Topics are defined inside the Gitfaas configuration. The
configuration file should be committed to the Git repo.
    """
    content_type = """
Gitfaas understands either JSON or pure text based on the content-type. Note that curl sends data by default with a
content-type set to x-www-form-urlencoded which is not supported.
    """
    show_starter = """
We can show you how to start your function in terms of code. Functions can retrieve the PAYLOAD sent to them via the
environment. They can also send back messages to the caller by making a request to Gitfaas itself. How to do theses things
in your program can be shown here. Don't forget to read the docs on the Gitfaas Github repo.
    """
    subjects = {
        "SCALE_TO_0": scale_to_0,
        "SCALE_TO_0_VALUE": scale_to_0_value,
        "FUNCTION_NAME": function_name,
        "MUST_RETRY": must_retry,
        "RETRIES": retries,
        "MUST_HAVE_VOLUME": must_have_volume,
        "VOLUME_SIZE": volume_size,
        "MUST_HAVE_NAMESPACE": must_have_namespace,
        "NAMESPACE_NAME": namespace_name,
        "IMAGE_NAME": image_name,
        "TOPIC_NAME": topic_name,
        "FILE_NAME": file_name,
        "PAYLOAD_TO_SEND": payload_to_send,
        "CONTENT_TYPE": content_type
    }

    @staticmethod
    def show_help_for(help_id):
        if help_id is not None:
            if help_id not in Help.subjects:
                raise ValueError(f"The given help_id does not exist in the available subjects. Got {help_id}.")
            print(Help.subjects[help_id])