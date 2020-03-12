FROM python:3.8.2-alpine3.10

RUN groupadd -r user && useradd -r -g user user
#ENV producer="123"
#ENV ADMIN="123"
USER user

WORKDIR /opt/app
COPY . .
RUN pip3 install -r req.txt
EXPOSE 5000

ENTRYPOINT ["python3", "./api_main.py"]








