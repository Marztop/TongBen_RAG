# Ragflow MinerU 集成 - 快速参考

## ⚡ 5分钟快速配置

### 1️⃣ 确认代理运行
```bash
docker ps | grep mineru-proxy
```

### 2️⃣ 测试连接
```bash
curl http://localhost:8081/openapi.json | jq '.info.title'
# 应返回: "MinerU Proxy API"
```

### 3️⃣ Ragflow 配置
- 打开 Ragflow → Settings → Model
- 添加 MinerU 模型
- **API Server**: `http://ublocal.marztop.cq.cn:8081`
- **Backend**: `pipeline` 或其他

### 4️⃣ 验证成功
- 创建 Knowledge Base
- 上传 PDF
- 验证是否成功解析

---

## 🔄 后端类型速查表

| 选择此后端 | 会使用此模型 | 场景 |
|---|---|---|
| `pipeline` | pipeline | ✅ 推荐，通用文档 |
| `vlm-http-client` | MinerU-HTML | HTML/网页文档 |
| `vlm-transformers` | vlm | VLM Transformers |
| `vlm-vllm-engine` | vlm | VLM vLLM 部署 |
| `vlm-mlx-engine` | vlm | VLM MLX 优化 |
| `vlm-vllm-async-engine` | vlm | VLM vLLM 异步 |
| `vlm-lmdeploy-engine` | vlm | VLM LMDeploy |

---

## 🧪 测试命令

```bash
# 检查 OpenAPI 规范
curl -s http://localhost:8081/openapi.json | jq '.paths | keys'

# 健康检查
curl http://localhost:8081/health

# 查看模型统计
curl http://localhost:8081/metrics

# 测试 API Key
curl -X POST http://localhost:8081/api/key/test

# 清空缓存
curl -X POST http://localhost:8081/cache/clear
```

---

## ❌ 常见问题

| 问题 | 解决方案 |
|---|---|
| 无法访问模型 | 检查 `/openapi.json` 端点是否返回 200 |
| 文档解析失败 | 验证 API Key 和网络连接 |
| 性能缓慢 | 检查缓存状态，清理过期数据 |
| 后端类型错误 | 使用推荐的 `pipeline` 后端 |

---

## 📊 监控

```bash
# 实时监控代理日志
docker logs -f mineru-proxy

# 获取性能指标
curl http://localhost:8081/metrics | jq '.models.stats'

# 获取缓存统计
curl http://localhost:8081/metrics | jq '.cache'
```

---

## 🔐 API Key 管理

```bash
# 打开 Web UI 管理
open http://localhost:8081/key/

# 或使用 API
curl -X GET http://localhost:8081/api/key          # 获取状态
curl -X POST http://localhost:8081/api/key \
  -H "Content-Type: application/json" \
  -d '{"key": "sk_test_..."}' # 设置 Key
curl -X DELETE http://localhost:8081/api/key       # 删除 Key
```

---

## 📝 关键点

✓ 代理自动处理所有 Ragflow 后端类型的映射  
✓ `/openapi.json` 端点必须返回 HTTP 200  
✓ 推荐使用 `pipeline` 后端（最稳定）  
✓ 支持 API Key 的 Web UI 管理  
✓ 自动缓存提高性能  

---

**最后更新**: 2026-03-28  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪
