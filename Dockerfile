FROM python:3.9-alpine


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


WORKDIR /app

# Install postgres client
RUN apk  add --update  postgresql-client

COPY requirements.txt .
RUN pip install  -r requirements.txt

COPY . .