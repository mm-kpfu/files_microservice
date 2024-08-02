FROM python:3.10

ENV PYTHONUNBUFFERED 1

ENV APP_HOME=/app

WORKDIR ${APP_HOME}/

COPY pip/requirements.txt .

RUN apt-get install libmagic1

RUN pip install -r requirements.txt

COPY . .
