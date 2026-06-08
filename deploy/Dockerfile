FROM python:3.12-slim

WORKDIR /app

COPY requirements-prod.txt .

RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

ENV PORT=8080

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
