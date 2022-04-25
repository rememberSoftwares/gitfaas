cd ./git
docker build . -t wingardiumleviosa/gitfaas-git:$1
docker tag gitfaas-git:$1 wingardiumleviosa/gitfaas-git:$1
docker push wingardiumleviosa/gitfaas-git:$1
echo "$1" > bap_git
