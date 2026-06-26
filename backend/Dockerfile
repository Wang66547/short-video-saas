# 后端 Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（ffmpeg等）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]