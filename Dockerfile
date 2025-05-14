
FROM python:3.10-slim

RUN apt-get update && apt-get install -y wget gnupg curl ca-certificates fonts-liberation \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 libxshmfence1 libgbm1 libgtk-3-0 libx11-xcb1

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m playwright install --with-deps

CMD ["python", "app.py"]
