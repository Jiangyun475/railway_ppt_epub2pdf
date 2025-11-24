FROM python:3.11-slim

# 安装 LibreOffice 和依赖
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建 templates 目录（如果不存在）
RUN mkdir -p templates

# 暴露端口
EXPOSE 5000

# 启动命令
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app