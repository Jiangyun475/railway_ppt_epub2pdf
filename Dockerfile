FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. 安装系统依赖
# 修正说明：
# 1. 移除了 ttf-wqy-microhei (旧包名，导致报错的原因)
# 2. 保留了 fonts-wqy-microhei (新包名)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    # LibreOffice 及其依赖
    libreoffice \
    libreoffice-writer \
    libreoffice-impress \
    default-jre \
    # WeasyPrint 依赖
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    shared-mime-info \
    # 中文字体 (精简并修正包名)
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    fonts-arphic-ukai \
    fonts-arphic-uming \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 复制应用代码
COPY . .

# 创建模板目录
RUN mkdir -p templates

# 暴露端口
EXPOSE 5000

# 启动命令
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level info app:app