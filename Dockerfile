FROM python:3.7.3-slim-stretch

RUN apt-get -y update && apt-get -y install gcc

WORKDIR /
COPY checkpoint /checkpoint

# Make changes to the requirements/app here.
# This Dockerfile order allows Docker to cache the checkpoint layer
# and improve build times if making changes.
RUN pip3 --no-cache-dir install starlette===0.14.0 uvicorn ujson openai python-dotenv newsapi-python spacy
RUN python3 -m spacy download en_core_web_sm

COPY app.py /

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENTRYPOINT ["python3", "-X", "utf8", "app.py"]
