FROM python:3.9.13

WORKDIR /usr/app

COPY . .
RUN pip3 install -r requirements.txt

CMD [ "python3", "main.py" ]