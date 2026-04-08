# Mineru 代理服务 - 快速启动指南

## ✅ 项目状态

- ✅ 所有源文件已创建
- ✅ Python虚拟环境已设置
- ✅ 所有依赖已安装
- ⏳ 待配置：MINERU_API_KEY

## 📝 第一步：配置API密钥

获取你的 Mineru API Key：
1. 访问 https://mineru.net/apiManage
2. 登录你的账号
3. 创建或复制已有的 API Key
4. 复制到下面的命令中执行：

```bash
cd /root/TongBen_RAG/mineru-proxy

# 设置 API 密钥（将 YOUR_API_KEY 替换为实际值）
export MINERU_API_KEY=YOUR_API_KEY

# 验证配置
echo "MINERU_API_KEY=$MINERU_API_KEY"
```

## 🚀 第二步：启动代理服务

### 方式1：直接运行

```bash
cd /root/TongBen_RAG/mineru-proxy
source venv/bin/activate
export MINERU_API_KEY=your_api_key_here
python app.py
```

### 方式2：使用启动脚本

```bash
cd /root/TongBen_RAG/mineru-proxy
export MINERU_API_KEY=your_api_key_here
./start.sh
```

等待输出：
```
✅ 服务启动在 http://0.0.0.0:5000
```

## 🧪 第三步：测试代理服务

打开**新终端**，运行：

```bash
cd /root/TongBen_RAG/mineru-proxy
source venv/bin/activate

# 完整测试（推荐）
python test_client.py

# 仅测试健康检查
python test_client.py --test-health

# 测试创建任务
python test_client.py --test-create

# 查询具体任务
python test_client.py --task-id your_task_id

# 测试大文件分片（需要提供PDF文件）
python test_client.py --test-chunking /path/to/large.pdf
```

## 📊 测试输出示例

```
============================================================
🚀 开始 Ragflow 代理API 测试
============================================================

=== 测试1: 健康检查 ===
✅ 响应码: 200
✅ 响应: {
  "status": "healthy",
  "timestamp": "2026-03-28T16:45:00.123456"
}

=== 测试2: 创建解析任务 (URL方式) ===
📤 请求: POST /api/v4/extract/task
📄 Payload: {
  "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
  "model_version": "vlm"
}
✅ 响应码: 200
✅ 成功创建任务: a90e6ab6-44f3-4554-b459-b62fe4c6b436
```

## 🔍 常见命令

```bash
# 进入项目目录
cd /root/TongBen_RAG/mineru-proxy

# 激活虚拟环境
source venv/bin/activate

# 查看日志（在启动服务的终端）
# 日志输出会实时显示所有请求和响应

# 清空缓存
curl -X POST http://localhost:5000/cache/clear

# 查看性能指标
curl http://localhost:5000/metrics | jq

# 健康检查
curl http://localhost:5000/health | jq

# 停止服务
# 在服务运行的终端按 Ctrl+C
```

## 🔧 配置调整

编辑 `.env` 文件可修改以下参数：

```bash
# 日志级别：DEBUG/INFO/WARNING/ERROR
LOG_LEVEL=INFO

# 缓存TTL（秒）
CACHE_TTL=3600

# 请求超时（秒）- 大文件可调整为60
REQUEST_TIMEOUT=30

# 大文件分片阈值
MAX_FILE_SIZE=209715200        # 200MB
MAX_PAGES=600
```

## 📚 API 端点速查表

| 端点 | 方法 | 用途 |
|-----|-----|-----|
| /health | GET | 健康检查 |
| /metrics | GET | 性能指标 |
| /cache/clear | POST | 清空缓存 |
| /api/v4/extract/task | POST | 创建解析任务 |
| /api/v4/extract/task/{id} | GET | 查询任务结果 |
| /api/v4/file-urls/batch | POST | 申请批量上传URL |
| /api/v4/extract-results/batch/{id} | GET | 查询批量结果 |
| /api/v4/extract/file-with-chunking | POST | 上传文件（自动分片） |
| /api/v1/agent/parse/url | POST | Agent轻量API-URL |
| /api/v1/agent/parse/file | POST | Agent轻量API-文件 |
| /api/v1/agent/parse/{id} | GET | Agent轻量API-查询 |

## 🌐 与Ragflow集成

启动代理服务后，修改Ragflow配置：

```python
# 在Ragflow的配置中
MINERU_APISERVER = "http://localhost:5000"  # 本机
# 或
MINERU_APISERVER = "http://mineru-proxy:5000"  # Docker环境
```

## ⚠️ 故障排查

### Q: "MINERU_API_KEY 未设置"
A: 运行 `export MINERU_API_KEY=your_key` 后再启动

### Q: "Connection refused"
A: 确保代理服务正在运行（检查服务所在终端输出）

### Q: 请求超时
A: 增加超时时间：`export REQUEST_TIMEOUT=60`

### Q: 缓存相关问题
A: 清空缓存：`curl -X POST http://localhost:5000/cache/clear`

## 📖 更多信息

- 详见 README.md - 完整文档
- 代码注释 - 各模块详细说明
- test_client.py - 完整测试示例

---

**准备好了吗？** 开始吧！

```bash
cd /root/TongBen_RAG/mineru-proxy
export MINERU_API_KEY=your_api_key_here
./start.sh
```

在另一个终端运行测试：
```bash
cd /root/TongBen_RAG/mineru-proxy
source venv/bin/activate
python test_client.py
```
