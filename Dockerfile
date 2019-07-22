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

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true
#RUN pip3 install gunicorn
#CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]

#RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:alex-p/tesseract-ocr
#RUN apt-get update && apt-get install -y tesseract-ocr-all 
# unblock port 80 for the Flask app to run on
#EXPOSE 5000

