from logger import logger

# 测试日志记录
logger.log_info("测试信息日志 - 不脱敏 API Key")
logger.log_request("POST", "https://mineru.net/api/test", 
                   {"Authorization": "Bearer sk-test-key-12345"}, 
                   '{"key": "value"}')
logger.log_response(200, '{"result": "success", "api_key": "sk-test-key-12345"}', 0.5)
logger.log_ragflow_request("test.pdf", 1024000, "vlm", 
                          {"backend": "vlm", "api_key": "sk-test-key-12345"})
print("✅ 日志测试完成")
