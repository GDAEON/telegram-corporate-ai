FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app

RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000

CMD ["bash", "run.sh"]