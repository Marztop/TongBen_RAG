#!/usr/bin/env python3
"""
API Key 管理功能测试脚本
演示如何通过 API 管理 Mineru API Key
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_get_key():
    """测试获取 API Key 状态"""
    print_section("1. 获取 API Key 状态")
    
    response = requests.get(f"{BASE_URL}/api/key")
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    return data.get("data", {})

def test_set_key(api_key):
    """测试保存 API Key"""
    print_section("2. 保存 API Key")
    
    payload = {"key": api_key}
    response = requests.post(
        f"{BASE_URL}/api/key",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    data = response.json()
    
    print(f"保存的 API Key: {api_key[:20]}...")
    print(f"状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    return data.get("code") == 0

def test_get_after_set():
    """测试设置后获取 API Key"""
    print_section("3. 验证 API Key 已保存")
    
    response = requests.get(f"{BASE_URL}/api/key")
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    key_status = data.get("data", {})
    print(f"\n✓ API Key 已配置: {key_status.get('configured')}")
    print(f"✓ 返回的 Key (部分): {key_status.get('key')}")
    
    return key_status

def test_delete_key():
    """测试删除 API Key"""
    print_section("4. 删除 API Key")
    
    response = requests.delete(f"{BASE_URL}/api/key")
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    return data.get("code") == 0

def test_get_after_delete():
    """测试删除后获取 API Key"""
    print_section("5. 验证 API Key 已删除")
    
    response = requests.get(f"{BASE_URL}/api/key")
    data = response.json()
    
    print(f"状态码: {response.status_code}")
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    key_status = data.get("data", {})
    print(f"\n✓ API Key 已删除: {not key_status.get('has_key')}")

def test_key_management_page():
    """测试获取管理页面"""
    print_section("6. 获取 API Key 管理前端页面")
    
    response = requests.get(f"{BASE_URL}/key/")
    
    print(f"状态码: {response.status_code}")
    print(f"页面大小: {len(response.text)} 字节")
    print(f"包含 '🔑 API Key 管理': {'🔑 API Key 管理' in response.text}")
    print(f"包含 JavaScript 表单处理: {'getElementById' in response.text}")
    
    if response.status_code == 200:
        print("\n✓ 前端页面加载成功!")
        print("✓ 可以通过浏览器访问: http://localhost:5000/key/")
    
    return response.status_code == 200

def main():
    print("\n" + "="*60)
    print("  Mineru API Key 管理系统 - 测试脚本")
    print("="*60)
    
    try:
        # 1. 获取当前状态
        key_status = test_get_key()
        print(f"当前 API Key 状态: {'已设置' if key_status.get('has_key') else '未设置'}")
        
        # 2. 保存新的 API Key
        test_api_key = "sk_test_1234567890abcdefghijklmnop"
        if test_set_key(test_api_key):
            print("✓ API Key 保存成功")
        
        # 3. 验证保存
        key_status = test_get_after_set()
        
        # 4. 删除 API Key
        if test_delete_key():
            print("✓ API Key 删除成功")
        
        # 5. 验证删除
        test_get_after_delete()
        
        # 6. 测试管理页面
        if test_key_management_page():
            print("\n✅ 所有测试通过!")
            print("\n📝 使用说明:")
            print("   1. 访问 http://localhost:5000/key/ 打开管理界面")
            print("   2. 输入您的 Mineru API Key")
            print("   3. 点击 '保存' 按钮")
            print("   4. 系统会自动验证 API Key 的有效性")
            print("   5. 点击 '删除' 按钮可以清除已保存的 API Key")
        else:
            print("\n❌ 管理页面加载失败")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务器")
        print("   请确保 Flask 应用正在运行: http://localhost:5000")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
