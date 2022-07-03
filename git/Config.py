#Logging options for the app. Choosing for instance INFO will only print logging.info(...) and above outputs
AVAILABLE_LOG_LEVELS = ["DEBUG", "INFO", "WARN"]

CLONE_FOLDER = "clone_folder"

# Shared path between the two containers. This volume is mounted by Kubernetes.
# The GIT repo is cloned inside this volume thus making the files available to the other container to apply.
# Must start with prepending "/"
VOLUME_MOUNT_PATH = "/pod-data"