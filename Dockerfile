FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG ENV_FILE=.env
COPY ${ENV_FILE} .env

COPY . .

EXPOSE 52357

CMD ["python", "main.py"]