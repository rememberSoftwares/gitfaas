docker build . -t wingardiumleviosa/demo-gitfaas-replace:$1
docker tag gitfaas-git:$1 wingardiumleviosa/demo-gitfaas-replace:$1
docker push wingardiumleviosa/demo-gitfaas-replace:$1
