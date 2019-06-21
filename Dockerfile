# this is an official Python runtime, used as the parent image
#FROM python:latest
FROM tesseractshadow/tesseract4re

# set the working directory in the container to /app
WORKDIR /app

# add the current directory to the container as /app
ADD src/ /app

# execute everyone's favorite pip command, pip install -r
#RUN pip install --trusted-host pypi.python.org -r requirements.txt
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update&&apt-get install python-opencv libsm6 libxext6 libxrender-dev libzbar-dev python3 python3-pip poppler-utils -y
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
#RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:alex-p/tesseract-ocr
#RUN apt-get update && apt-get install -y tesseract-ocr-all 
# unblock port 80 for the Flask app to run on
#EXPOSE 5000

