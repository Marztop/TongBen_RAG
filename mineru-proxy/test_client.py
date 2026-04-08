#!/usr/bin/env python3
"""
Ragflow 模拟客户端 - 用于测试Mineru代理API
"""

import requests
import time
import json
import sys
from pathlib import Path

class RagflowTestClient:
    """模拟Ragflow的测试客户端"""
    
    def __init__(self, proxy_url: str = "http://localhost:5000"):
        self.proxy_url = proxy_url
        self.session = requests.Session()
    
    def test_health(self):
        """测试健康检查"""
        print("\n=== 测试1: 健康检查 ===")
        try:
            resp = self.session.get(f"{self.proxy_url}/health")
            print(f"✅ 响应码: {resp.status_code}")
            print(f"✅ 响应: {json.dumps(resp.json(), indent=2)}")
            return True
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_create_extract_task(self, url="https://cdn-mineru.openxlab.org.cn/demo/example.pdf"):
        """测试创建单文件解析任务"""
        print("\n=== 测试2: 创建解析任务 (URL方式) ===")
        try:
            payload = {
                "url": url,
                "model_version": "vlm"
            }
            print(f"📤 请求: POST /api/v4/extract/task")
            print(f"📄 Payload: {json.dumps(payload, indent=2)}")
            
            resp = self.session.post(
                f"{self.proxy_url}/api/v4/extract/task",
                json=payload,
                timeout=30
            )
            print(f"✅ 响应码: {resp.status_code}")
            result = resp.json()
            print(f"✅ 响应: {json.dumps(result, indent=2)}")
            
            if result.get("code") == 0:
                task_id = result["data"]["task_id"]
                print(f"✅ 成功创建任务: {task_id}")
                return task_id
            else:
                print(f"❌ 创建失败: {result.get('msg')}")
                return None
        except Exception as e:
            print(f"❌ 错误: {e}")
            return None
    
    def test_get_task_result(self, task_id, max_attempts=30):
        """轮询查询任务结果"""
        print(f"\n=== 测试3: 查询任务结果 (task_id: {task_id[:8] if task_id else 'N/A'}...) ===")
        
        for attempt in range(max_attempts):
            try:
                print(f"\n📤 轮询请求 #{attempt + 1}/{max_attempts}")
                resp = self.session.get(
                    f"{self.proxy_url}/api/v4/extract/task/{task_id}",
                    timeout=30
                )
                print(f"✅ 响应码: {resp.status_code}")
                result = resp.json()
                
                state = result.get("data", {}).get("state")
                print(f"⏳ 任务状态: {state}")
                
                if state == "done":
                    print(f"✅ 任务完成!")
                    print(f"✅ 完整响应: {json.dumps(result, indent=2)}")
                    return result["data"]
                elif state == "failed":
                    err_msg = result.get("data", {}).get("err_msg")
                    print(f"❌ 任务失败: {err_msg}")
                    return None
                else:
                    print(f"⏳ 任务进行中... 等待5秒后重新查询")
                    time.sleep(5)
            
            except Exception as e:
                print(f"❌ 错误: {e}")
                return None
        
        print(f"❌ 轮询超时 ({max_attempts} 次尝试)")
        return None
    
    def test_batch_upload_urls(self):
        """测试申请批量上传URL"""
        print("\n=== 测试4: 申请批量上传URL ===")
        try:
            payload = {
                "files": [
                    {"name": "document1.pdf", "data_id": "doc_001"},
                    {"name": "document2.pdf", "data_id": "doc_002"}
                ],
                "model_version": "vlm"
            }
            print(f"📤 请求: POST /api/v4/file-urls/batch")
            print(f"📄 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            resp = self.session.post(
                f"{self.proxy_url}/api/v4/file-urls/batch",
                json=payload,
                timeout=30
            )
            print(f"✅ 响应码: {resp.status_code}")
            result = resp.json()
            print(f"✅ 响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get("code") == 0:
                batch_id = result["data"]["batch_id"]
                file_urls = result["data"]["file_urls"]
                print(f"✅ 批量ID: {batch_id}")
                print(f"✅ 获得 {len(file_urls)} 个上传URL")
                return batch_id, file_urls
            return None
        except Exception as e:
            print(f"❌ 错误: {e}")
            return None
    
    def test_metrics(self):
        """测试性能指标"""
        print("\n=== 测试5: 查看性能指标 ===")
        try:
            resp = self.session.get(f"{self.proxy_url}/metrics")
            print(f"✅ 响应码: {resp.status_code}")
            result = resp.json()
            print(f"✅ 指标: {json.dumps(result, indent=2)}")
            return True
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_agent_api(self):
        """测试Agent轻量API"""
        print("\n=== 测试6: Agent轻量API ===")
        try:
            payload = {
                "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
                "language": "ch"
            }
            print(f"📤 请求: POST /api/v1/agent/parse/url")
            print(f"📄 Payload: {json.dumps(payload, indent=2)}")
            
            resp = self.session.post(
                f"{self.proxy_url}/api/v1/agent/parse/url",
                json=payload,
                timeout=30
            )
            print(f"✅ 响应码: {resp.status_code}")
            result = resp.json()
            print(f"✅ 响应: {json.dumps(result, indent=2)}")
            return result.get("code") == 0
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def test_large_file_chunking(self, sample_pdf_path=None):
        """测试大文件分片处理"""
        print("\n=== 测试7: 大文件分片处理 ===")
        
        if not sample_pdf_path:
            print("⚠️  跳过: 未提供PDF文件路径")
            print("    使用方法: python test_client.py --test-chunking /path/to/large.pdf")
            return False
        
        if not Path(sample_pdf_path).exists():
            print(f"❌ 文件不存在: {sample_pdf_path}")
            return False
        
        try:
            with open(sample_pdf_path, 'rb') as f:
                files = {'file': (Path(sample_pdf_path).name, f)}
                data = {'model_version': 'vlm'}
                
                print(f"📤 上传文件: {Path(sample_pdf_path).name}")
                resp = self.session.post(
                    f"{self.proxy_url}/api/v4/extract/file-with-chunking",
                    files=files,
                    data=data,
                    timeout=60
                )
                print(f"✅ 响应码: {resp.status_code}")
                result = resp.json()
                print(f"✅ 响应: {json.dumps(result, indent=2)}")
                return result.get("code") == 0
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def run_full_test(self):
        """运行完整测试流程"""
        print("=" * 60)
        print("🚀 开始 Ragflow 代理API 测试")
        print("=" * 60)
        
        # 测试1: 健康检查
        if not self.test_health():
            print("\n❌ 健康检查失败，请确保代理服务运行中")
            return False
        
        # 测试2: 创建任务
        task_id = self.test_create_extract_task()
        if not task_id:
            print("\n⚠️  创建任务失败")
        else:
            # 测试3: 查询结果
            self.test_get_task_result(task_id, max_attempts=3)
        
        # 测试4: 申请批量上传URL
        batch_result = self.test_batch_upload_urls()
        if not batch_result:
            print("\n⚠️  申请批量URL失败")
        
        # 测试5: 性能指标
        self.test_metrics()
        
        # 测试6: Agent轻量API
        self.test_agent_api()
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Ragflow Mineru代理API测试客户端')
    parser.add_argument('--proxy-url', default='http://localhost:5000', 
                       help='代理服务URL (默认: http://localhost:5000)')
    parser.add_argument('--test-health', action='store_true', help='仅测试健康检查')
    parser.add_argument('--test-create', action='store_true', help='测试创建任务')
    parser.add_argument('--test-chunking', metavar='PDF_PATH', 
                       help='测试大文件分片处理')
    parser.add_argument('--task-id', help='查询指定的任务ID')
    
    args = parser.parse_args()
    
    client = RagflowTestClient(args.proxy_url)
    
    if args.test_health:
        client.test_health()
    elif args.test_create:
        task_id = client.test_create_extract_task()
        if task_id:
            time.sleep(3)
            client.test_get_task_result(task_id, max_attempts=5)
    elif args.test_chunking:
        client.test_large_file_chunking(args.test_chunking)
    elif args.task_id:
        client.test_get_task_result(args.task_id, max_attempts=5)
    else:
        client.run_full_test()

if __name__ == '__main__':
    main()
