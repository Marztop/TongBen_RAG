#!/usr/bin/env python3
"""
测试 Ragflow 后端类型映射
"""
import sys
sys.path.insert(0, '/root/TongBen_RAG/mineru-proxy')

from model_handler import handler

# 测试后端类型映射
test_cases = [
    ("pipeline", "pipeline"),
    ("vlm-http-client", "MinerU-HTML"),
    ("vlm-transformers", "vlm"),
    ("vlm-vllm-engine", "vlm"),
    ("vlm-mlx-engine", "vlm"),
    ("vlm-vllm-async-engine", "vlm"),
    ("vlm-lmdeploy-engine", "vlm"),
    ("vlm", "vlm"),  # 直接指定官方模型
    ("MinerU-HTML", "MinerU-HTML"),  # 直接指定官方模型
]

print("=" * 80)
print("测试 Ragflow 后端类型映射")
print("=" * 80)

passed = 0
failed = 0

for backend_type, expected_model in test_cases:
    try:
        result = handler.validate_model(backend_type)
        if result == expected_model:
            print(f"✓ '{backend_type}' → '{result}' (预期: '{expected_model}')")
            passed += 1
        else:
            print(f"✗ '{backend_type}' → '{result}' (预期: '{expected_model}')")
            failed += 1
    except Exception as e:
        print(f"✗ '{backend_type}' 抛出异常: {e}")
        failed += 1

print("=" * 80)
print(f"测试结果: {passed} 通过, {failed} 失败")
print("=" * 80)

if failed == 0:
    print("✓ 所有映射测试通过！")
    sys.exit(0)
else:
    print("✗ 某些测试失败")
    sys.exit(1)
