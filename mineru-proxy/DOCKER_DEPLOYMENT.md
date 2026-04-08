# Docker 部署指南

## 概述

Mineru Proxy 现已完全支持 Docker 部署，可在 8081 端口运行，所有配置通过 `.env` 文件管理。

## 环境信息

- **Docker 镜像**: `mineru-proxy:latest`
- **容器端口**: `8081`
- **主机映射**:
  - `./cache:/app/cache` - 缓存目录（持久化）
  - `./keys.json:/app/keys.json` - API Key 存储
  - `./logs:/app/logs` - 日志文件

## 快速开始

### 1. 配置 .env

编辑 `.env` 文件设置参数：

```bash
# API 服务配置
MINERU_API_URL=https://mineru.net
PROXY_PORT=8081                    # Docker 内部端口
PROXY_HOST=0.0.0.0
DOCKER_PROXY_PORT=8081             # 主机映射端口

# 日志配置
LOG_LEVEL=INFO

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=3600

# 请求配置
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# 临时文件
TEMP_DIR=/tmp/mineru_proxy
```

### 2. 启动容器

#### 方法 A：直接使用 docker run

```bash
cd /root/TongBen_RAG/mineru-proxy

docker build -t mineru-proxy:latest .

docker run -d \
  --name mineru-proxy \
  -p 8081:8081 \
  -e PROXY_PORT=8081 \
  -e PROXY_HOST=0.0.0.0 \
  -e LOG_LEVEL=INFO \
  -e CACHE_ENABLED=true \
  -e CACHE_TTL=3600 \
  -v $PWD/cache:/app/cache \
  -v $PWD/keys.json:/app/keys.json \
  -v $PWD/logs:/app/logs \
  --restart unless-stopped \
  mineru-proxy:latest
```

#### 方法 B：使用 docker-compose

```bash
docker-compose up -d
```

### 3. 验证服务

```bash
# 检查容器状态
docker ps | grep mineru-proxy

# 测试健康检查
curl http://localhost:8081/health

# 查看日志
docker logs mineru-proxy
```

## 配置管理

### 访问管理界面

打开浏览器访问：

```
http://localhost:8081/key/
```

![API Key 管理界面](./screenshots/key-management-docker.png)

### API Key 管理 API

```bash
# 获取状态
curl http://localhost:8081/api/key

# 保存 API Key
curl -X POST http://localhost:8081/api/key \
  -H "Content-Type: application/json" \
  -d '{"key":"your_api_key_here"}'

# 删除 API Key
curl -X DELETE http://localhost:8081/api/key

# 测试连接
curl -X POST http://localhost:8081/api/key/test
```

## 容器管理

### 查看容器日志

```bash
# 查看实时日志
docker logs -f mineru-proxy

# 查看最后 100 行
docker logs --tail 100 mineru-proxy

# 查看时间戳包含的日志
docker logs --timestamps mineru-proxy
```

### 重启容器

```bash
# 重启服务
docker restart mineru-proxy

# 完全重新创建（保留卷）
docker stop mineru-proxy
docker rm mineru-proxy
docker run -d ...  # 运行启动命令
```

### 进入容器

```bash
# 进入容器 shell
docker exec -it mineru-proxy /bin/bash

# 在容器内查看 keys.json
docker exec mineru-proxy cat /app/keys.json

# 在容器内查看缓存
docker exec mineru-proxy ls -la /app/cache/
```

### 停止和删除

```bash
# 停止容器
docker stop mineru-proxy

# 删除容器（保留卷）
docker rm mineru-proxy

# 删除镜像
docker rmi mineru-proxy:latest
```

## 卷管理

### 缓存持久化

缓存目录映射到主机：

```
主机: ./cache
容器: /app/cache

主机路径: /root/TongBen_RAG/mineru-proxy/cache
```

查看缓存文件：

```bash
ls -lh /root/TongBen_RAG/mineru-proxy/cache/

# 示例输出
# -rw-r--r-- 1.8M cache/中医耳鼻喉科常见病诊断指南_result.zip
# -rw-r--r-- 389B cache/task_1a6e95ee-d987-464a.json
```

### API Key 持久化

API Key 保存在 keys.json：

```
主机: ./keys.json
容器: /app/keys.json

内容示例:
{
  "mineru_api_key": "sk_your_key_here"
}
```

### 日志持久化

日志文件映射到主机：

```
主机: ./logs
容器: /app/logs
```

## 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROXY_PORT` | 8081 | 容器内监听端口 |
| `PROXY_HOST` | 0.0.0.0 | 监听地址 |
| `MINERU_API_URL` | https://mineru.net | 官方 API 地址 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `CACHE_ENABLED` | true | 是否启用缓存 |
| `CACHE_TTL` | 3600 | 缓存过期时间（秒） |
| `REQUEST_TIMEOUT` | 30 | 请求超时时间（秒） |
| `MAX_RETRIES` | 3 | 最大重试次数 |
| `TEMP_DIR` | /tmp/mineru_proxy | 临时文件目录 |

## Ragflow 集成

配置 Ragflow 使用此代理：

```bash
# docker-compose.yaml
services:
  ragflow:
    environment:
      - MINERU_APISERVER=http://mineru-proxy:8081
      # MINERU_API_KEY 不再需要在这里设置
    
    # 如果 mineru-proxy 也在 Docker Compose 中
    depends_on:
      - mineru-proxy
```

或通过 Ragflow UI 配置：

1. 打开 Ragflow 后台管理
2. 进入系统设置 → Mineru 配置
3. 设置 API 服务器地址为: `http://mineru-proxy:8081`
4. 点击保存

## 故障排查

### 问题：容器无法启动

**解决方案：**

```bash
# 查看错误日志
docker logs mineru-proxy

# 检查端口是否被占用
netstat -tlnp | grep 8081

# 如果被占用，改变映射端口
docker run -d \
  -p 8082:8081 \  # 改为 8082
  ...
```

### 问题：无法连接到 API

**解决方案：**

```bash
# 检查容器是否正在运行
docker ps | grep mineru-proxy

# 检查网络连接
docker exec mineru-proxy curl localhost:8081/health

# 检查防火墙
sudo ufw allow 8081
```

### 问题：API Key 保存后不生效

**解决方案：**

```bash
# 检查 keys.json 是否已保存
cat /root/TongBen_RAG/mineru-proxy/keys.json

# 检查容器内的文件
docker exec mineru-proxy cat /app/keys.json

# 重启容器
docker restart mineru-proxy
```

### 问题：缓存数据丢失

**解决方案：**

```bash
# 检查卷映射
docker inspect mineru-proxy | grep -A 20 Mounts

# 确保 cache 目录存在
mkdir -p /root/TongBen_RAG/mineru-proxy/cache

# 检查文件权限
ls -la /root/TongBen_RAG/mineru-proxy/cache/
```

## 性能优化

### 多工人配置

Dockerfile 中已配置 4 个 gunicorn workers。如需调整：

```bash
# 编辑 Dockerfile 中的 CMD
CMD gunicorn --bind 0.0.0.0:${PROXY_PORT} --workers 8 app:app
```

### 资源限制

```bash
docker run -d \
  --memory=512m \
  --cpus=1.0 \
  ...
```

### 日志轮转

创建 logging 驱动配置：

```bash
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  ...
```

## 更新 Docker 镜像

当代码更新时：

```bash
# 停止现有容器
docker stop mineru-proxy

# 删除旧镜像
docker rmi mineru-proxy:latest

# 重新构建
docker build -t mineru-proxy:latest .

# 启动新容器
docker run -d ...
```

## 监控和维护

### 查看容器资源使用

```bash
docker stats mineru-proxy
```

### 导出日志

```bash
docker logs mineru-proxy > /tmp/mineru-proxy.log
```

### 容器备份

```bash
# 保存容器快照
docker commit mineru-proxy mineru-proxy:backup

# 导出镜像
docker save mineru-proxy:latest | gzip > mineru-proxy.tar.gz

# 导入镜像
gunzip -c mineru-proxy.tar.gz | docker load
```

## 生产部署建议

1. **使用私有镜像仓库** - 存储 mineru-proxy 镜像
2. **配置 reverse proxy** - 使用 Nginx 作为反向代理
3. **启用 TLS/SSL** - 用 HTTPS 保护 API
4. **监控和告警** - 使用 Prometheus + Grafana
5. **备份策略** - 定期备份 `keys.json` 和 `cache/`
6. **日志收集** - 使用 ELK Stack 或 Loki 收集日志
7. **容器编排** - 考虑使用 Kubernetes 部署

## 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Gunicorn 配置](https://docs.gunicorn.org/)
- [Mineru API 文档](https://mineru.net/api/docs)
