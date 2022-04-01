FROM ubuntu:20.04

WORKDIR /src

RUN apt-get update
RUN apt-get install -y python3 python3-pip

COPY mediaire_toolbox /src/mediaire_toolbox
COPY _mediaire_toolbox/requirements.txt /src/requirements.txt
RUN pip3 install -r requirements.txt

COPY main.py /src/main.py

CMD ["python3", "main.py"]
