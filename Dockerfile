FROM python:3.8.2-alpine3.10

#ENV producer="123"
#ENV ADMIN="123"

WORKDIR /opt/app
COPY . .
RUN pip3 install -r requirements.txt
EXPOSE 8081

ENTRYPOINT ["python3", "./Api_main.py"]








