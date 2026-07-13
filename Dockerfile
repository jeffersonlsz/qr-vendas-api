FROM python:3.12-slim

WORKDIR /app

COPY requirements-prod.txt .

RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port ${PORT}