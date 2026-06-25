FROM python:3.12-slim

# Запрещаем Python создавать .pyc файлы (__pycache__).
ENV PYTHONDONTWRITEBYTECODE=1
# Отключае буферизацию stdout/stderr.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# build-essential: Набор build tools для C расширений (psycopg2, cryptography).
# libpq-dev:       Набор для PostgreSQL (psycopg2).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./

RUN pip install --upgrade pip \
    && pip install ".[dev]"

COPY . .