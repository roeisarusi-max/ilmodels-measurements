FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libxkbcommon0 libxrandr2 libgbm1 libpango-1.0-0 \
    libpangocairo-1.0-0 libcairo2 libxcb1 libx11-6 libxext6 \
    libxfixes3 libxrender1 libasound2 libopus0 libvpx7 libwebp6 \
    libwoff1 libharfbuzz0b libhyphen0 libgstreamer1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chromium

# Copy application
COPY . .

# Run scraper on startup, then start server
CMD python3 AUTO_SCRAPER.py || true && python3 ilmodels_measurements.py
