
```

# localhost dev

docker build -t find-my-clones-dev -f Dockerfile .
docker run -it -p 9000:8080 \
    -w /workdir -v $PWD:/workdir find-my-clones bash


# zappa with venv

sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install python3.8-dev python3.8-venv -yq
python3.8 -m venv myvenv
source myvenv/bin/activate

echo $(openssl rand -hex 4)
append above to s3_bucket in `zappa_settings.json`

pip install zappa
pip install -r requirements.txt

stage: prod
s3: zappa-find-my-clones

zappa init
zappa deploy prod
zappa update prod


zappa undeploy dev --remove-logs

--

https://aws.amazon.com/getting-started/hands-on/build-serverless-web-app-lambda-apigateway-s3-dynamodb-cognito/


https://docs.aws.amazon.com/lambda/latest/dg/urls-tutorial.html
https://github.com/zappa/Zappa
https://ianwhitestone.work/zappa-serverless-docker/
https://ianwhitestone.work/zappa-serverless-docker/

```
