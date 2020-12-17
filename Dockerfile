FROM arm32v6/python:3.9.1-alpine3.12

RUN mkdir activ8

ENV MONGO_HOST "host.docker.internal"

ADD requirements.txt activ8/

RUN pip3 install -r activ8/requirements.txt

ADD main.py activ8/
ADD mongo_client.py activ8/

ENTRYPOINT cd activ8 && python3 main.py