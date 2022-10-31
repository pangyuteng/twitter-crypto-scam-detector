FROM ubuntu:20.04
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3 python3-pip

WORKDIR /opt
COPY requirements.txt .
RUN pip3 install -r requirements.txt