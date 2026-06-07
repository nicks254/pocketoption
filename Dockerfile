FROM python:3.11-slim

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1 \
    fonts-liberation \
    libdbus-1-3 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright
RUN pip install --no-cache-dir playwright

# Install Chromium browser
RUN playwright install chromium --with-deps

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "tyltest.py"]
