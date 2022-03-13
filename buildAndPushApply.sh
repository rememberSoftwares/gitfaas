cd ./applier
docker build . -t apply:$1
docker tag $1 wingardiumleviosa/gitfaas/apply:$1
docker push wingardiumleviosa/gitfaas/apply:$1
