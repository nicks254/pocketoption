FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget curl gnupg libnss3 libnspr4 libdbus-1-1 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright
RUN playwright install chromium --with-deps

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "tyltest.py"]
