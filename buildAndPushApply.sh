cd ./applier
docker build . -t petrificustotalus/gitfaas-apply:$1
docker tag gitfaas-apply:$1 petrificustotalus/gitfaas-apply:$1
docker push petrificustotalus/gitfaas-apply:$1
echo "$1" >> bap_apply
