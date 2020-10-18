FROM ubuntu:20.04
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3 python3-pip
RUN ln -s /usr/bin/python3 /usr/bin/python & \
    ln -s /usr/bin/pip3 /usr/bin/pip
WORKDIR /opt
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY apikey.yml .
