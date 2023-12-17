cd ./git
docker build . -t petrificustotalus/gitfaas-git:$1
docker tag gitfaas-git:$1 petrificustotalus/gitfaas-git:$1
docker push petrificustotalus/gitfaas-git:$1
echo "$1" > bap_git
