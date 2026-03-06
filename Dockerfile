FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md requirements-dev.txt ./
COPY app ./app

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements-dev.txt

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
