FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000 8081

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV PROXY_PORT=${PROXY_PORT:-5000}

SHELL ["/bin/bash", "-c"]
CMD ["bash", "-c", "gunicorn --bind 0.0.0.0:${PROXY_PORT:-5000} --timeout 120 --workers 4 app:app"]
