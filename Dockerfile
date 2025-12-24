# 使用官方 Python 运行时作为父镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件到容器中
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Node.js 和 npm
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# 安装前端依赖
WORKDIR /app/frontend
RUN npm install

# 回到主目录
WORKDIR /app

# 暴露端口
EXPOSE 3000 5000 5001 5002 8765

# 启动命令
CMD ["sh", "-c", "cd backend && python app.py & python publish.py & python subscribe.py & python data_address.py & cd ../frontend && npm run dev"]