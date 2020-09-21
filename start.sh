#!/bin/bash
docker-compose up --scale celery=3 --scale web=2