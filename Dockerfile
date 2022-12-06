FROM python:3.7-alpine

COPY . /app

WORKDIR /app

COPY requirements.txt /app 

RUN pip3 install --no-cache-dir -r /app/requirements.txt

CMD ["python3", "app.py"]