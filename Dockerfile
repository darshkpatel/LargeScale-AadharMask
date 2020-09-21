FROM tesseractshadow/tesseract4re

# set the working directory in the container to /app
WORKDIR /app

# add the current directory to the container as /app
ADD src/ /app

# execute everyone's favorite pip command, pip install -r
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update&&apt-get install python-opencv libsm6 libxext6 libxrender-dev libzbar-dev python3 python3-pip poppler-utils -y
RUN pip3 install --trusted-host pypi.python.org -r requirements.txt

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true
