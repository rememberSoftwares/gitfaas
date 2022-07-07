docker build . -t wingardiumleviosa/demo-reversed-sleep:$1
docker tag gitfaas-git:$1 wingardiumleviosa/demo-reversed-sleep:$1
docker push wingardiumleviosa/demo-reversed-sleep:$1
echo "$1" > bap_demo
