FROM python:3.11.3

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install Django==5.0 djangorestframework==3.14.0 pandas==2.1.4 openpyxl==3.1.2 psycopg2==2.9.9 numpy==1.26.2

COPY . .

EXPOSE 8000

ENTRYPOINT [ "/app/django.sh" ]