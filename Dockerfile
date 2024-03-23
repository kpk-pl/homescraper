FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3 python3-pip

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN apt-get install -y firefox

WORKDIR /opt/scrape
ENTRYPOINT /opt/scrape/scrape.py

