FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py config.py Procfile runtime.txt ./
COPY app ./app
COPY skills ./skills
COPY tools ./tools
COPY knowledge ./knowledge
COPY specs ./specs
COPY config ./config
COPY personas ./personas
COPY design-systems ./design-systems

RUN mkdir -p data public/reports public/content public/reviews

EXPOSE 8000

CMD ["python", "main.py"]
