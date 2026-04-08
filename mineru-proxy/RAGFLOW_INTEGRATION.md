# Ragflow 集成指南

## 与 Ragflow 的集成方式

本代理提供了两种集成方式与 Ragflow 配合使用：

### 方式1: 官方API方式（推荐）- 直接修改配置

这是最简单的方式，只需修改 Ragflow 配置指向代理即可：

```bash
# 在 Ragflow docker/.env 中设置
MINERU_APISERVER = "http://mineru-proxy:5000"
MINERU_API_KEY = "your_official_api_key"
```

**工作流程：**
```
Ragflow → 代理 → 官方Mineru API → 返回full_zip_url 
    ↓
代理自动下载ZIP文件
    ↓
返回ZIP流给Ragflow
```

### 方式2: 本地Mineru模拟方式 - `/file_parse` 端点

代理提供了与本地Mineru完全兼容的 `/file_parse` 端点，这样Ragflow就可以像使用本地Mineru一样工作。

## 核心改进点

### 🎯 Ragflow 接收文件流，而非URL

| 官方API返回 | 之前代理 | 现在代理 |
|----------|--------|--------|
| `full_zip_url` | ❌ 返回URL | ✅ 下载后返回ZIP流 |
| 类型 | JSON+URL | **ZIP二进制文件** |
| Ragflow使用 | ❌ 无法直接用 | ✅ 直接处理 |

### 🔄 新增接口：`/file_parse` (Ragflow兼容)

```http
POST /file_parse HTTP/1.1
Content-Type: multipart/form-data

files: <PDF文件>
backend: vlm
output_dir: ./output
lang_list: zh,en
...

---
Response:
HTTP/1.1 200 OK
Content-Type: application/zip

<ZIP文件流>
```

## 集成步骤

### 步骤1：启动代理服务

```bash
cd /root/TongBen_RAG/mineru-proxy
source venv/bin/activate
python app.py
```

### 步骤2：配置Ragflow

**选项A - 使用官方API（推荐）：**

编辑 `docker/.env`：
```bash
MINERU_APISERVER=http://mineru-proxy:5000
MINERU_API_KEY=<your_official_mineru_api_key>
```

重启Ragflow：
```bash
cd ragflow/docker
docker compose down
docker compose up -d
```

**选项B - 使用本地Mineru方式：**

修改Ragflow的后端配置以使用 `/file_parse` 端点：
```bash
MINERU_APISERVER=http://mineru-proxy:5000/file_parse
```

### 步骤3：验证集成

1. 在Ragflow中上传PDF文件
2. 选择Mineru作为解析引擎
3. 等待处理完成

## API端点总览

### 📋 官方API兼容端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v4/extract/task` | POST | 创建解析任务（URL方式） |
| `/api/v4/extract/task/{id}` | GET | 查询任务结果（返回JSON+URL） |
| `/api/v4/extract/task/{id}/zip` | GET | 下载任务结果ZIP文件 |
| `/api/v4/file-urls/batch` | POST | 申请批量上传URL |
| `/api/v4/extract-results/batch/{id}` | GET | 查询批量任务结果 |

### 🎯 Ragflow兼容端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/file_parse` | POST | **Ragflow直接使用**，上传PDF → 返回ZIP流 |

### 🔍 监控端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/metrics` | GET | 性能指标（缓存、模型统计） |
| `/cache/clear` | POST | 清空缓存 |

## Ragflow 工作流程说明

### 使用官方API时（推荐）

```
1. Ragflow 发送PDF URL → 代理
2. 代理转发到官方API
3. 官方API 返回 full_zip_url
4. 代理自动下载ZIP
5. 代理返回ZIP流给Ragflow
6. Ragflow 解压处理
```

### 使用 /file_parse 接口时

```
1. Ragflow POST /file_parse (上传PDF)
2. 代理内部流程：
   a. 申请上传URL
   b. 上传文件到S3
   c. 轮询等待处理
   d. 下载ZIP
3. 代理返回ZIP流
4. Ragflow 解压处理
```

## 缓存特性

- ✅ 自动缓存所有 /api/v4/ 的GET请求
- ✅ 缓存有效期：1小时
- ✅ 磁盘持久化：cache/ 目录
- ✅ 查看缓存：`curl http://localhost:5000/metrics`

## 性能指标

### 文件处理时间

| 规模 | 时间 | 备注 |
|------|------|------|
| 小文件 (<50MB) | ~3-10秒 | 官方API处理 |
| 中文件 (50-200MB) | ~10-30秒 | 官方API处理 + 下载 |
| 大文件 (>200MB) | ~30-120秒 | 自动分片 + 合并 |
| 缓存命中 | ~100-500ms | 本地返回 |

### 网络消耗

- 上传：PDF文件大小
- 下载：ZIP解析结果（通常 5-20% 的原文件大小）
- 缓存后：仅缓存查询（几KB）

## 故障排查

### 问题1：Ragflow无法连接代理

```bash
# 检查代理服务
curl http://localhost:5000/health

# 检查网络连接
docker exec ragflow-backend ping mineru-proxy
```

### 问题2：文件上传超时

增加超时时间（app.py中）：
```python
timeout=300  # 改为更大值（秒）
```

### 问题3：ZIP下载失败

检查日志：
```bash
tail -f /tmp/flask.log | grep "\[Ragflow\]"
```

## 常见问题

**Q: 需要修改Ragflow源代码吗？**
A: 不需要。只需修改 Ragflow 的环境变量 `MINERU_APISERVER` 指向代理即可。

**Q: 代理支持哪些Mineru模型？**
A: 支持 `vlm`, `pipeline`, `MinerU-HTML` 等，自动选择最优模型。

**Q: 可以处理超大文件吗？**
A: 可以。代理会自动分片处理 >200MB 或 >600页的PDF，然后合并结果。

**Q: 缓存会占用多少磁盘？**
A: 每个缓存项约 1-5KB，1000个缓存项约占 5-10MB。

