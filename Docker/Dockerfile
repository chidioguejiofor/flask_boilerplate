ARG PYTHON_VERSION=3.7-slim

# Set base image
FROM python:${PYTHON_VERSION} as builder

# Set maintainer
LABEL maintainer='Victor Nwokeocha'

# Python unbuffered env and python dont write byte code variable
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y wget netcat supervisor

# Upgrade and install pipenv
RUN pip install --upgrade pip && pip install pipenv

WORKDIR /usr/src/app

# creation of requirements.txt
COPY ./Pipfile* ./

# Install dependencies
RUN pipenv install --system  --deploy --ignore-pipfile

# Copy all the files from local to docker
COPY ./ ./

# Copy supervisor file
COPY ./Docker/supervisor.conf /usr/local/etc/supervisord.conf

RUN chmod +x ./Docker/entrypoint.sh

# Create a user to run the app on docker
RUN useradd -r -u 1234 -U docker-user

# Change the ownership of the working dir to the new user
# and give write access to the folder.
RUN chown -R docker-user:docker-user ./ && chmod 755 ./

# Switch to the new user
USER docker-user

ENTRYPOINT ["/bin/bash", "./Docker/entrypoint.sh"]

EXPOSE 5000
