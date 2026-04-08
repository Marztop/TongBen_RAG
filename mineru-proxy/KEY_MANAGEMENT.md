# API Key 管理系统

## 功能说明

这个系统允许用户通过 Web 界面管理 Mineru API Key，无需修改 `.env` 文件或重启服务。

### 特点

- ✅ **Web 管理界面**: 友好的前端页面管理 API Key
- ✅ **实时验证**: 保存时自动测试 API Key 的有效性
- ✅ **本地存储**: API Key 保存在本地的 `keys.json` 文件
- ✅ **安全隐蔽**: 返回 API Key 时只显示前 10 个字符
- ✅ **动态加载**: 无需重启就能使用新的 API Key
- ✅ **RESTful API**: 提供完整的 REST API 供程序集成

## 使用方式

### 1. 通过 Web 界面（推荐）

访问以下 URL 打开管理界面：

```
http://localhost:5000/key/
```

![API Key 管理界面](./screenshots/key-management.png)

**操作步骤：**

1. 在输入框中输入您的 Mineru API Key
2. 点击 **💾 保存** 按钮
3. 系统会自动验证 API Key
4. 验证成功后，您会看到状态显示 "✅ 已设置"
5. 点击 **🗑️ 删除** 可以清除已保存的 API Key

### 2. 通过 REST API

#### 获取 API Key 状态

```bash
curl http://localhost:5000/api/key
```

响应示例：
```json
{
  "code": 0,
  "data": {
    "configured": true,
    "has_key": true,
    "key": "sk_test_12..."
  },
  "msg": "ok",
  "trace_id": "2026-03-28T17:22:42.741634"
}
```

#### 保存 API Key

```bash
curl -X POST http://localhost:5000/api/key \
  -H "Content-Type: application/json" \
  -d '{"key":"your_api_key_here"}'
```

#### 删除 API Key

```bash
curl -X DELETE http://localhost:5000/api/key
```

#### 测试 API Key 有效性

```bash
curl -X POST http://localhost:5000/api/key/test
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `key_manager.py` | API Key 管理模块，处理文件读写 |
| `templates/key_management.html` | Web 管理界面前端 |
| `keys.json` | API Key 存储文件（本地存储）|
| `test_key_management.py` | API Key 管理功能测试脚本 |

## 安全注意事项

- ✅ API Key 只在本地存储，不上传到任何服务器
- ✅ API Key 从不以明文返回给前端
- ✅ 前端只显示 API Key 的前 10 个字符
- ✅ 修改 `.env` 中的 `MINERU_API_KEY` 不会覆盖已保存的 Key
- ⚠️ 此系统仅适用于本地开发，如部署到生产环境需要加密存储

## 工作流程

```
用户输入 API Key
      ↓
点击保存按钮
      ↓
前端发送到后端 /api/key
      ↓
后端保存到 keys.json
      ↓
测试 API 连接
      ↓
返回验证结果
      ↓
前端显示成功/失败提示
```

## 原理说明

### 动态 API Key 加载

系统在每次请求时都会动态读取当前的 API Key：

1. `mineru_client.py` 调用 `key_manager.get_api_key()`
2. 优先使用 `keys.json` 中保存的 Key
3. 如果没有保存的 Key，则使用 `.env` 中的默认 Key
4. 这样确保新保存的 Key 立即生效

```python
def _get_api_key(self) -> str:
    """获取当前 API key（支持动态更新）"""
    from key_manager import get_api_key
    key = get_api_key()
    if not key:
        key = Config.MINERU_API_KEY
    return key
```

## 故障排除

### 问题：无法访问管理界面

**解决方案：**
- 确保 Flask 应用正在运行：`ps aux | grep python`
- 检查服务是否监听在 `0.0.0.0:5000`：`netstat -tlnp | grep 5000`

### 问题：保存 API Key 后仍然收到认证错误

**解决方案：**
- 检查 `keys.json` 是否存在：`ls -la keys.json`
- 验证 API Key 格式是否正确
- 在管理界面点击 **测试连接** 按钮验证 Key 的有效性

### 问题：API Key 显示为 null

**解决方案：**
- 确保已成功保存 API Key
- 刷新页面重新加载
- 检查浏览器控制台的错误信息

## 测试

运行测试脚本验证所有功能：

```bash
cd /root/TongBen_RAG/mineru-proxy
source venv/bin/activate
python test_key_management.py
```

## 与 Ragflow 集成

配置 Ragflow 使用此代理时，API Key 已经在此系统中管理：

```bash
# Ragflow docker-compose 配置
MINERU_APISERVER=http://mineru-proxy:5000
# MINERU_API_KEY 不再需要在这里配置
```

API Key 会通过 `/key/` 管理界面配置。

## 常见问题

**Q: 如果我在 `.env` 中设置了 `MINERU_API_KEY`，会被使用吗？**

A: 系统会优先使用 `keys.json` 中保存的 Key。如果 `keys.json` 中没有 Key，才会使用 `.env` 中的 Key。

**Q: 我可以在多个服务器上使用相同的 `keys.json` 吗？**

A: 可以，但建议每个服务器独立配置，以便于管理和审计。

**Q: API Key 是否加密存储？**

A: 目前以明文方式存储在 `keys.json` 中。如需加密，请修改 `key_manager.py`。

## 后续改进

- [ ] 添加 API Key 的加密存储
- [ ] 支持多个 API Key 管理
- [ ] 添加 API Key 使用统计
- [ ] 支持 API Key 过期时间设置
- [ ] 添加 Web UI 的暗色主题

## 联系方式

如有问题或建议，请联系开发团队。
