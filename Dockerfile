FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    # WeasyPrint 依赖
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    shared-mime-info \
    # 中文字体
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建目录
RUN mkdir -p templates

# 暴露端口
EXPOSE 5000

# 启动命令
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info app:app