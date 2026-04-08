# Ragflow MinerU 代理集成指南

## 概述

本文档说明如何在 Ragflow 中配置 MinerU 代理，以及代理如何处理不同的后端类型。

## 🚀 快速开始

### 前置条件

- MinerU 代理已启动，监听 `http://ublocal.marztop.cq.cn:8081`
- Ragflow 已启动并可访问
- 代理返回 HTTP 200 的 `/openapi.json` 端点

### Ragflow 配置步骤

1. **打开 Ragflow UI**
   - 导航到 "Settings" (设置) → "Model" (模型)

2. **添加 MinerU 模型**
   - 点击 "Add Model" (添加模型)
   - 选择 "MinerU"

3. **填写配置参数**
   ```
   Model Name: mineru-proxy (或任何标识名称)
   API Server: http://ublocal.marztop.cq.cn:8081
   Backend: pipeline (推荐，见后文说明)
   Output Directory: (可选)
   Delete Output: ✓ (推荐勾选)
   ```

4. **验证连接**
   - Ragflow 自动发送 HEAD/GET 请求到 `/openapi.json`
   - 如果返回 HTTP 200，配置成功

## 📋 后端类型映射

代理支持 Ragflow 的所有后端类型，并将其映射到官方 MinerU API 支持的模型类型。

### 映射规则

| Ragflow 后端类型 | 映射到 API 模型 | 说明 |
|---|---|---|
| `pipeline` | `pipeline` | MinerU 标准 Pipeline 处理流程 |
| `vlm-http-client` | `MinerU-HTML` | VLM HTTP 客户端（HTML 模式） |
| `vlm-transformers` | `vlm` | VLM Transformers 引擎 |
| `vlm-vllm-engine` | `vlm` | VLM vLLM 引擎 |
| `vlm-mlx-engine` | `vlm` | VLM MLX 引擎 |
| `vlm-vllm-async-engine` | `vlm` | VLM vLLM Async 引擎 |
| `vlm-lmdeploy-engine` | `vlm` | VLM LMDeploy 引擎 |

### 推荐配置

- **生产环境**: `pipeline` - 最稳定、最保险的选择
- **HTML 处理**: `vlm-http-client` - 当需要 HTML 输出时使用
- **VLM 处理**: 其他 `vlm-*` 类型 - 根据您的 VLM 部署环境选择

## 🔧 工作原理

### 请求流程

```
Ragflow 发送请求
    ↓
代理接收 (backend_type, files, ...)
    ↓
后端类型映射 (pipeline, vlm, MinerU-HTML)
    ↓
转发到官方 MinerU API
    ↓
返回结果给 Ragflow
```

### 示例请求

**Ragflow 发送的请求体** (使用 `pipeline` 后端):
```json
{
  "files": [
    {
      "name": "document.pdf",
      "size": 1024000
    }
  ],
  "model_version": "pipeline"
}
```

**代理处理流程**:
1. 收到 `model_version: "pipeline"`
2. 验证和映射：`"pipeline"` → `"pipeline"` (无需映射)
3. 发送到官方 API: 同样使用 `"pipeline"`

**另一个示例** (使用 `vlm-transformers` 后端):
```json
{
  "files": [...],
  "model_version": "vlm-transformers"
}
```

**代理处理流程**:
1. 收到 `model_version: "vlm-transformers"`
2. 验证和映射：`"vlm-transformers"` → `"vlm"`
3. 发送到官方 API: 使用 `"vlm"`

## ✅ 验证集成

### 1. 检查 OpenAPI 规范端点

```bash
curl http://ublocal.marztop.cq.cn:8081/openapi.json | jq '.info'
```

应返回:
```json
{
  "title": "MinerU Proxy API",
  "description": "Proxy service for MinerU document parsing",
  "version": "1.0.0",
  "contact": {
    "name": "MinerU Proxy",
    "url": "https://github.com/infiniflow/mineru-proxy"
  }
}
```

### 2. 健康检查

```bash
curl http://ublocal.marztop.cq.cn:8081/health
```

应返回:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-28T17:59:48.123456"
}
```

### 3. 测试后端映射

在 Ragflow UI 中进行测试：
- 创建 Knowledge Base
- 上传 PDF 文件
- 选择 MinerU 模型和不同的后端类型
- 验证文档是否成功解析

## 📊 监控和统计

代理提供统计信息端点:

```bash
curl http://ublocal.marztop.cq.cn:8081/metrics
```

应返回:
```json
{
  "cache": {
    "hits": 10,
    "misses": 5,
    "entries": 3
  },
  "models": {
    "default_model": "vlm",
    "stats": {
      "pipeline": 5,
      "vlm": 8,
      "MinerU-HTML": 2
    }
  }
}
```

## 🐛 故障排查

### 问题：Ragflow 无法访问模型

**错误信息**:
```
Fail to access model(MinerU/mineru-proxy).[MinerU] MinerU API not accessible: 
http://ublocal.marztop.cq.cn:8081/openapi.json
```

**解决方案**:
1. 验证代理是否运行: `curl http://ublocal.marztop.cq.cn:8081/health`
2. 验证 `/openapi.json` 端点: `curl http://ublocal.marztop.cq.cn:8081/openapi.json`
3. 检查网络连接: `ping ublocal.marztop.cq.cn`
4. 检查防火墙规则

### 问题：文档解析失败

**调试步骤**:
1. 检查代理日志: `docker logs mineru-proxy | tail -50`
2. 验证 API Key 是否正确设置
3. 测试 API Key: `curl -X POST http://localhost:8081/api/key/test`
4. 查看是否有缓存问题: `curl -X POST http://localhost:8081/cache/clear`

## 📚 相关端点

| 端点 | 功能 |
|---|---|
| `GET /openapi.json` | 返回 OpenAPI 3.0 规范 |
| `GET /health` | 健康检查 |
| `GET /metrics` | 统计信息 |
| `POST /cache/clear` | 清空缓存 |
| `GET /api/key` | 获取 API Key 状态 |
| `POST /api/key` | 设置 API Key |
| `DELETE /api/key` | 删除 API Key |
| `POST /api/key/test` | 测试 API Key |

## 🔐 API Key 管理

代理支持通过 Web UI 管理 API Key：

```bash
# 打开 API Key 管理页面
open http://localhost:8081/key/

# 或通过 API 管理
curl -X GET http://localhost:8081/api/key
curl -X POST http://localhost:8081/api/key -H "Content-Type: application/json" -d '{"key": "sk_..."}'
curl -X DELETE http://localhost:8081/api/key
```

## 📝 注意事项

1. **模型版本非必填**: 如果 Ragflow 未指定 `model_version`，代理将使用默认模型 `vlm`
2. **后端类型验证**: 代理会自动验证 Ragflow 发送的后端类型，并进行必要的映射
3. **缓存机制**: 同一文件的多次请求会使用缓存，提高性能
4. **错误处理**: 所有的错误都会被记录在日志中，方便故障排查

## 🎯 最佳实践

1. **选择合适的后端**: 
   - 通用场景: `pipeline`
   - HTML 文档: `vlm-http-client`
   - 特殊优化: 其他 `vlm-*` 类型

2. **监控和观察**:
   - 定期检查 `/metrics` 端点
   - 监控缓存命中率
   - 追踪模型使用统计

3. **维护和升级**:
   - 定期更新 MinerU API
   - 保持代理依赖包最新
   - 定期清理缓存

## 📞 技术支持

如有问题或建议，请：
1. 查看 MinerU 官方文档
2. 查看 Ragflow 官方文档
3. 检查代理日志获取详细错误信息
