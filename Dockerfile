FROM python:3.13-slim

WORKDIR /app

# 安裝基本工具和 Chrome 依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# 添加 Google Chrome 的來源並安裝
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*


# 安裝 Poetry
RUN pip install --no-cache-dir poetry

# 複製 Poetry 配置文件
COPY pyproject.toml ./

# 安裝 Python 依賴
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-root

# 複製應用程式碼
COPY src/ ./src/
COPY .env ./

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 執行應用程式
CMD ["python", "src/autoauth/main.py"]