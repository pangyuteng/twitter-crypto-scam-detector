
```

# localhost dev

docker build -t find-my-clones .
docker run -it -p 5000:5000 -w /opt -v $PWD:/opt find-my-clones bash
python app.py


# TODO: deploy via aws?

https://aws.amazon.com/getting-started/hands-on/build-serverless-web-app-lambda-apigateway-s3-dynamodb-cognito/

```