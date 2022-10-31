

# use lambda to serve front and back.

docker build -t find-my-clones .
docker run -it -p 5000:5000 -w /opt -v $PWD:/opt find-my-clones bash

# /

# index.html
# get query
# get results
# front end calls
