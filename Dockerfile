FROM python:3.11-slim

# Chrome Browser ইনস্টল করুন
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Chrome এর জন্য key যোগ করুন
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /etc/apt/trusted.gpg.d/google.gpg
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Chrome Browser ইনস্টল করুন
RUN apt-get update && apt-get install -y google-chrome-stable

# ChromeDriver ম্যানুয়ালি ইনস্টল করুন (সঠিক ভার্সন)
RUN CHROME_VER=$(google-chrome --version | awk '{print $3}') && \
    echo "Chrome version: $CHROME_VER" && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VER}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir selenium python-telegram-bot

COPY bolt.py .

CMD ["python", "bolt.py"]