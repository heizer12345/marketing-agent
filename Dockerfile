FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install deps first (layer cache)
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# App code (frontend/ excluded via .dockerignore)
COPY . .

RUN mkdir -p data public/reports public/content public/reviews personas design-systems

EXPOSE 8000

CMD ["python", "main.py"]
