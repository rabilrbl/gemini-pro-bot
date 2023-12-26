FROM python:3.12-alpine as builder

RUN pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt


FROM python:3.12-alpine as base

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

WORKDIR /app

ENTRYPOINT ["python", "main.py"]
