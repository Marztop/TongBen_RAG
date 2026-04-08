#!/usr/bin/env python3
"""
测试 Ragflow 兼容的 /file_parse 端点
"""

import requests
import sys
import os
from pathlib import Path

def test_file_parse_endpoint():
    """测试 /file_parse 端点"""
    
    print("\n" + "="*70)
    print("🧪 测试 Ragflow 兼容的 /file_parse 端点")
    print("="*70)
    
    proxy_url = "http://localhost:5000"
    
    # 下载示例PDF
    print("\n📥 下载示例PDF...")
    try:
        pdf_url = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        pdf_content = response.content
        print(f"✅ 下载成功 ({len(pdf_content)} bytes)")
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False
    
    # 上传到代理的 /file_parse 端点
    print("\n📤 上传PDF到代理的 /file_parse 端点...")
    print(f"   点为：POST {proxy_url}/file_parse")
    
    try:
        # 准备文件
        files = {
            'files': ('example.pdf', pdf_content, 'application/pdf')
        }
        
        # 发送请求
        response = requests.post(
            f"{proxy_url}/file_parse",
            files=files,
            data={
                'backend': 'vlm',
                'output_dir': './output',
                'lang_list': 'zh,en'
            },
            timeout=600,  # 10分钟超时
            stream=True
        )
        
        print(f"✅ 响应码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 请求失败")
            print(f"   响应: {response.text}")
            return False
        
        # 检查返回类型
        content_type = response.headers.get('Content-Type', '')
        print(f"✅ 返回类型: {content_type}")
        
        if 'zip' not in content_type.lower():
            print(f"❌ 返回类型不是ZIP")
            return False
        
        # 保存ZIP文件
        output_dir = Path("./test_output")
        output_dir.mkdir(exist_ok=True)
        
        zip_file = output_dir / "result.zip"
        with open(zip_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = zip_file.stat().st_size
        print(f"✅ ZIP文件已保存: {zip_file}")
        print(f"   文件大小: {file_size} bytes")
        
        # 解压检查
        print("\n🔍 检查ZIP内容...")
        try:
            import zipfile
            with zipfile.ZipFile(zip_file, 'r') as z:
                file_list = z.namelist()
                print(f"✅ ZIP包含 {len(file_list)} 个文件:")
                for file in sorted(file_list)[:10]:  # 显示前10个
                    print(f"   - {file}")
                if len(file_list) > 10:
                    print(f"   ... 和 {len(file_list) - 10} 个其他文件")
        except Exception as e:
            print(f"❌ 解压失败: {e}")
            return False
        
        print("\n✅ 测试成功！")
        print("\n📋 总结:")
        print(f"   1️⃣ 代理接收PDF文件")
        print(f"   2️⃣ 代理转发到官方Mineru API")
        print(f"   3️⃣ 代理下载解析结果ZIP")
        print(f"   4️⃣ 代理返回ZIP流给客户端")
        print(f"\n✨ 这样Ragflow就可以直接接收ZIP文件了！")
        
        return True
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（>10分钟）")
        print(f"   官方API处理时间较长，请稍后重试")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_file_parse_endpoint()
    sys.exit(0 if success else 1)
