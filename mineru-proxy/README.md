# Mineru 官方API代理服务

为Ragflow提供的Mineru官方API代理层，支持大文件自动分片处理。

## 功能特性

- ✅ 完整转发Mineru v4精准解析API
- ✅ 支持Agent轻量API (v1)
- ✅ 内存缓存优化性能
- ✅ **大文件自动分片** (>200MB或>600页自动分割)
- ✅ 分片任务并行处理和自动合并  
- ✅ 多模型支持 (pipeline/vlm/MinerU-HTML)
- ✅ 结构化日志记录
- ✅ 性能监控指标

## 快速开始

### 前置要求
- Python 3.10+
- Mineru官方API Token (申请地址: https://mineru.net/apiManage)

### 虚拟环境安装

```bash
# 进入项目目录
cd /root/TongBen_RAG/mineru-proxy

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 MINERU_API_KEY
export MINERU_API_KEY=your_api_key_here
```

### 本地运行

```bash
python app.py
```

访问 http://localhost:5000/health 验证服务运行正常

### Docker运行

```bash
# 确保.env已配置
docker-compose up -d
```

## API 端点

### 精准解析 API (v4)

#### 创建单文件解析任务
```bash
POST /api/v4/extract/task
{
  "url": "https://...",
  "model_version": "vlm"  # pipeline|vlm|MinerU-HTML
}
```

#### 查询任务结果  
```bash
GET /api/v4/extract/task/{task_id}
```

#### 申请批量上传URL
```bash
POST /api/v4/file-urls/batch
{
  "files": [{"name": "doc.pdf", "data_id": "abc"}],
  "model_version": "vlm"
}
```

#### 获取批量任务结果
```bash
GET /api/v4/extract-results/batch/{batch_id}
```

### ⭐ 大文件分片处理

#### 上传PDF（自动分片）
```bash
POST /api/v4/extract/file-with-chunking

参数: file (multipart)
      model_version (form data)

响应示例:
{
  "code": 0,
  "data": {
    "batch_ids": ["batch_1", "batch_2", "batch_3"],
    "chunks": 3,
    "info": "file split into 3 chunks"
  }
}
```

当文件超过**200MB**或**600页**时自动触发分片处理，返回多个batch_ids用于轮询。

### Agent轻量 API (v1)

```bash
POST /api/v1/agent/parse/url
POST /api/v1/agent/parse/file
GET /api/v1/agent/parse/{task_id}
```

### 监控端点

```bash
GET /health           # 健康检查
GET /metrics          # 性能指标
POST /cache/clear     # 清空缓存
```

## 测试

### 运行完整测试
```bash
chmod +x test_client.py
python test_client.py --proxy-url http://localhost:5000
```

### 测试大文件分片
```bash
python test_client.py --test-chunking /path/to/large_file.pdf
```

### 查询指定任务
```bash
python test_client.py --task-id your_task_id
```

## 配置选项

编辑 `.env` 文件：

```bash
# 官方API认证（必需）
MINERU_API_KEY=your_token_here

# 服务配置
PROXY_PORT=5000
PROXY_HOST=0.0.0.0
LOG_LEVEL=INFO

# 大文件分片
MAX_FILE_SIZE=209715200        # 200MB
MAX_PAGES=600
CHUNK_SIZE=104857600          # 100MB per chunk
MAX_PAGES_PER_CHUNK=300

# 缓存
CACHE_ENABLED=true
CACHE_TTL=3600

# 请求
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# 临时文件
TEMP_DIR=/tmp/mineru_proxy
```

## 与Ragflow集成

修改Ragflow配置，使用代理地址：

```python
# 在Ragflow中配置如下
MINERU_APISERVER = "http://mineru-proxy:5000"
MINERU_API_KEY = "your_api_key"
```

## 架构说明

### 文件分片流程

```
大文件上传 (>200MB或>600页)
    ↓
检测文件大小和页数
    ↓
需要分片? ──NO→ 直接上传到官方API
    │
   YES
    ↓
按100MB/300页分割PDF
    ↓
并行为每个分片创建任务
    ↓
轮询所有分片任务完成
    ↓
合并所有分片结果
    ├─ 合并Markdown内容
    ├─ 合并JSON结构
    └─ 收集所有图片资源
    ↓
返回统一ZIP包给Ragflow
```

### 缓存策略

- GET请求结果自动缓存（1小时TTL）
- 按task_id/batch_id缓存结果
- 任务完成时自动缓存，减少轮询压力
- 监控端点 `/cache/clear` 可手动清除

### 日志记录

所有请求/响应自动记录，敏感信息（token、key）自动脱敏，便于排查问题。

## 文件结构

```
mineru-proxy/
├── app.py                 # Flask主应用
├── config.py              # 配置管理
├── cache.py               # 缓存系统
├── logger.py              # 日志系统
├── mineru_client.py       # API客户端
├── file_processor.py      # 文件分片处理
├── model_handler.py       # 多模型支持
├── requirements.txt       # 依赖清单
├── Dockerfile            # 容器镜像
├── docker-compose.yml    # Docker编排
├── .env.example          # 环境变量模板
├── test_client.py        # 测试客户端
└── README.md             # 本文档
```

## 故障排查

### 无法连接到官方API

检查：
- MINERU_API_KEY 是否正确设置
- 网络是否可访问 https://mineru.net
- 请求超时设置 (DEFAULT_TIMEOUT = 30s)

### 大文件上传超时

增加REQUEST_TIMEOUT环境变量：
```bash
export REQUEST_TIMEOUT=60
```

### 缓存相关问题

清空缓存：
```bash
curl -X POST http://localhost:5000/cache/clear
```

## 许可证

MIT
