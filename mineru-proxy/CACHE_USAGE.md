# 缓存系统使用说明

## 概述

本项目已实现**内存 + 磁盘双层缓存**系统，所有来自官方API的返回内容会自动保存到本地磁盘，方便测试和调试。

## 缓存工作流程

```
请求 → API调用 → 官方API返回
                    ↓
              ├→ 保存到内存（快速读取）
              └→ 保存到磁盘（数据持久化）
```

## 缓存文件位置

所有缓存文件保存在项目目录下的 `cache/` 文件夹：

```
mineru-proxy/
├── app.py
├── cache/                          ← 缓存目录
│   ├── task_xxx.json              ← 单个任务缓存
│   ├── batch_xxx.json             ← 批量任务缓存
│   ├── agent_xxx.json             ← Agent API缓存
│   └── ...
├── venv/
└── ...
```

## 缓存文件格式

每个JSON文件包含完整的API返回信息：

### 文件名规则
- 单个任务：`task_{task_id}.json`
- 批量任务：`batch_{batch_id}.json`
- Agent任务：`agent_{task_id}.json`

### 文件内容示例

```json
{
  "key": "task_f755d5a5-657a-4c62-827a-e66e98c722b9",
  "value": {
    "task_id": "f755d5a5-657a-4c62-827a-e66e98c722b9",
    "state": "done",
    "err_msg": "",
    "full_zip_url": "https://cdn-mineru.openxlab.org.cn/pdf/2026-03-13/1d3cc28b-aaff-4881-ab2b-3384d7b1b335.zip"
  },
  "created_at": "2026-03-28T17:00:56.272207",
  "ttl": 3600,
  "expires_at": "2026-03-28T18:00:56.272221"
}
```

**字段说明：**
- `key` - 缓存键标识
- `value` - 官方API返回的完整数据
- `created_at` - 缓存创建时间
- `ttl` - 缓存有效期（秒）
- `expires_at` - 缓存过期时间

## 缓存行为

### ✅ 什么会被缓存

| 端点 | 方法 | 缓存条件 | 文件名 |
|------|------|--------|-------|
| `/api/v4/extract/task/{id}` | GET | 状态为"done" | `task_{id}.json` |
| `/api/v4/extract-results/batch/{id}` | GET | 所有任务"done" | `batch_{id}.json` |
| `/api/v1/agent/parse/{id}` | GET | 状态为"done" | `agent_{id}.json` |

### ❌ 什么不会被缓存

- POST请求（创建任务）
- 未完成的任务（state != "done"）
- 错误响应

## 使用场景

### 1️⃣ 查看缓存数据

```bash
# 查看所有缓存文件
ls -lah cache/

# 查看特定任务的缓存
cat cache/task_xxx.json | python -m json.tool

# 搜索最新的缓存文件
ls -lt cache/ | head -5
```

### 2️⃣ 测试时重复使用缓存

缓存自动在内存中，相同task_id的重复查询**立即返回**（无需再次调用官方API）：

```bash
# 第一次查询　→ 调用官方API，保存缓存
curl http://localhost:5000/api/v4/extract/task/task_123

# 第二次查询　→ 直接从缓存返回（毫秒级）
curl http://localhost:5000/api/v4/extract/task/task_123
```

### 3️⃣ 离线测试

使用缓存的JSON数据进行离线测试：

```python
import json

# 加载缓存数据
with open('cache/task_xxx.json') as f:
    cache_data = json.load(f)
    result = cache_data['value']
    
print(result['full_zip_url'])
```

### 4️⃣ 查看缓存统计

```bash
curl http://localhost:5000/metrics | python -m json.tool
```

输出示例：
```json
{
  "cache": {
    "cache_dir": "/root/TongBen_RAG/mineru-proxy/cache",
    "total_keys_memory": 2,      ← 内存中的缓存数
    "total_keys_disk": 2,        ← 磁盘上的缓存文件数
    "expired_keys": 0            ← 已过期的缓存
  }
}
```

### 5️⃣ 清空缓存

```bash
# 清空所有缓存（内存 + 磁盘）
curl -X POST http://localhost:5000/cache/clear

# 或者手动删除
rm -f cache/*.json
```

## 缓存有效期

- **默认TTL**: 1小时（3600秒）
- **可配置**: 在 `config.py` 中修改 `CACHE_TTL`

过期的缓存文件会在以下情况自动清理：
- 查询时发现过期 → 从磁盘删除
- 调用 `/cache/clear` → 全部清空
- 手动删除 `cache/` 目录

## 性能提升

### 缓存命中时间对比

| 操作 | 时间 | 备注 |
|------|------|------|
| 官方API调用 | ~3-5秒 | 网络延迟 + 处理 |
| 内存缓存 | ~1-10ms | 直接返回 |
| 磁盘加载 | ~50-100ms | 文件读取 + JSON解析 |

## 与Ragflow集成

当集成到Ragflow时，缓存会自动收集所有解析数据：

```bash
# 启动proxy
MINERU_APISERVER=http://localhost:5000 \
MINERU_API_KEY=your_key \
python app.py

# Ragflow请求会自动缓存结果
# cache/ 目录会逐渐积累历史数据用于分析
```

## 故障排查

### 缓存目录不存在

缓存目录会在Flask启动时自动创建，如果没有创建，检查：
```bash
mkdir -p /root/TongBen_RAG/mineru-proxy/cache
```

### 缓存文件损坏

如果JSON文件格式错误，直接删除即可重新生成：
```bash
rm cache/task_xxx.json
# 重新查询该任务会重新缓存
```

### 缓存未保存

检查权限和磁盘空间：
```bash
# 检查目录权限
ls -ld cache/

# 检查磁盘空间
du -sh cache/
df -lh
```

## 总结

| 特性 | 说明 |
|------|------|
| 📂 存储位置 | `./cache/*.json` |
| 💾 持久化 | 磁盘自动保存 |
| ⚡ 性能 | 内存缓存毫秒级读取 |
| ⏱️ 有效期 | 1小时（可配置） |
| 🔍 查询 | `/metrics` 查看统计 |
| 🗑️ 清空 | `POST /cache/clear` |
| 🧪 测试 | 完整数据本地分析 |

