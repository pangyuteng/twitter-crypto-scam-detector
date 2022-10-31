# find-my-clones

Find twitter profiles containing your name and a similar profile pic.

[demo link](https://www.aigonewrong.com/find-my-clones)


```


developer notebook:

docker build -t tweetbot .
docker run -it -p 8888:8888 -v $PWD:/opt tweetbot bash
jupyter notebook --ip=* --port=8888 --allow-root

```
