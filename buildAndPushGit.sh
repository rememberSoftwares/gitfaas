cd ./git
docker build . -t git:$1
docker tag $1 wingardiumleviosa/gitfaas/git:$1
docker push wingardiumleviosa/gitfaas/git:$1
