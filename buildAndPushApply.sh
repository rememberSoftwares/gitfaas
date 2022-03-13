cd ./applier
docker build . -t wingardiumleviosa/gitfaas-apply:$1
docker tag gitfaas-apply:$1 wingardiumleviosa/gitfaas-apply:$1
docker push wingardiumleviosa/gitfaas-apply:$1
