FROM python:3.8

COPY ./src /src
WORKDIR /src

RUN pip3 install -r requirements.txt

CMD ["python3", "wsgi.py"]