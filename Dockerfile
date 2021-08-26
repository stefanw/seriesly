FROM python:3.9-slim-buster

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE seriesly.settings


RUN mkdir /code && useradd -m -r seriesly && \
    chown seriesly /code

COPY requirements.txt /code/
RUN pip install -r /code/requirements.txt
COPY seriesly /code/seriesly

COPY manage.py /code/
COPY Procfile /code/

ARG GIT_HASH
ENV GIT_HASH=${GIT_HASH:-dev}

USER seriesly

WORKDIR /code/
EXPOSE 8000
