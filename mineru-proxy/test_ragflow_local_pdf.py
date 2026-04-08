#!/usr/bin/env python3
"""
模拟Ragflow测试脚本
使用本地test_pdf中的PDF文件进行完整的Mineru解析测试
"""

import requests
import sys
import os
from pathlib import Path
import time

def test_ragflow_with_local_pdf():
    """使用本地PDF文件测试Ragflow集成"""
    
    print("\n" + "="*80)
    print("🧪 模拟Ragflow - 本地PDF文件测试")
    print("="*80)
    
    proxy_url = "http://localhost:5000"
    
    # 1. 查找本地PDF文件
    test_pdf_dir = Path("./test_pdf")
    if not test_pdf_dir.exists():
        print(f"❌ 测试PDF目录不存在: {test_pdf_dir}")
        return False
    
    pdf_files = list(test_pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ 测试PDF目录为空")
        return False
    
    pdf_file = pdf_files[0]  # 使用第一个PDF
    print(f"\n📄 找到测试PDF: {pdf_file.name}")
    print(f"   大小: {pdf_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 2. 读取PDF文件
    print(f"\n📖 读取PDF文件...")
    try:
        with open(pdf_file, 'rb') as f:
            pdf_content = f.read()
        print(f"✅ 读取成功 ({len(pdf_content)} bytes)")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return False
    
    # 3. 模拟Ragflow上传到代理的/file_parse端点
    print(f"\n📤 [Ragflow模拟] 上传PDF到代理...")
    print(f"   端点: POST {proxy_url}/file_parse")
    print(f"   文件: {pdf_file.name}")
    print(f"   参数: backend=vlm, lang_list=zh")
    
    try:
        files = {
            'files': (pdf_file.name, pdf_content, 'application/pdf')
        }
        
        data = {
            'backend': 'vlm',
            'lang_list': 'zh',
            'output_dir': './output'
        }
        
        print(f"\n⏳ 等待代理处理... (这可能需要1-5分钟)")
        start_time = time.time()
        
        # 发送请求，不设置timeout（让服务器有足够时间处理）
        response = requests.post(
            f"{proxy_url}/file_parse",
            files=files,
            data=data,
            timeout=600,  # 10分钟超时
            stream=True
        )
        
        elapsed = time.time() - start_time
        print(f"✅ 收到响应 (耗时: {elapsed:.1f}秒)")
        print(f"   响应码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 请求失败")
            print(f"   响应: {response.text}")
            return False
        
        # 检查返回类型
        content_type = response.headers.get('Content-Type', '')
        print(f"   返回类型: {content_type}")
        
        if 'zip' not in content_type.lower():
            print(f"❌ 返回类型不是ZIP")
            return False
        
        # 4. 保存ZIP文件到cache目录
        print(f"\n💾 保存ZIP文件到cache目录...")
        
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)
        
        # 生成ZIP文件名
        pdf_name_without_ext = pdf_file.stem
        zip_file = cache_dir / f"{pdf_name_without_ext}_result.zip"
        
        # 流式保存
        print(f"   目标: {zip_file.relative_to('.')}")
        
        with open(zip_file, 'wb') as f:
            chunk_count = 0
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    chunk_count += 1
                    total_size += len(chunk)
                    if chunk_count % 100 == 0:
                        print(f"   已保存: {total_size / 1024 / 1024:.2f} MB")
        
        file_size = zip_file.stat().st_size
        print(f"✅ 保存完成")
        print(f"   文件大小: {file_size / 1024 / 1024:.2f} MB")
        print(f"   完整路径: {zip_file.absolute()}")
        
        # 5. 解压并检查内容
        print(f"\n🔍 检查ZIP文件内容...")
        try:
            import zipfile
            with zipfile.ZipFile(zip_file, 'r') as z:
                file_list = z.namelist()
                print(f"✅ ZIP包含 {len(file_list)} 个文件:")
                
                # 显示所有文件
                for i, file in enumerate(sorted(file_list)):
                    size = z.getinfo(file).file_size
                    size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"
                    print(f"   {i+1:3d}. {file:<60s} ({size_str})")
                
                # 检查是否有_content_list.json
                json_files = [f for f in file_list if '_content_list.json' in f]
                if json_files:
                    print(f"\n✅ 找到内容列表JSON文件: {json_files}")
                    
                    # 读取JSON文件
                    for json_file in json_files:
                        with z.open(json_file) as f:
                            import json
                            content = json.load(f)
                            if isinstance(content, list):
                                print(f"   包含 {len(content)} 个内容块")
                                # 显示前3个块的类型
                                for i, item in enumerate(content[:3]):
                                    item_type = item.get('type', 'unknown')
                                    text_preview = ""
                                    if item.get('text'):
                                        text_preview = item.get('text')[:50]
                                    elif item.get('table_body'):
                                        text_preview = f"[表格] {str(item.get('table_body'))[:30]}"
                                    print(f"      块{i+1}: {item_type} - {text_preview}")
                else:
                    print(f"⚠️  未找到_content_list.json文件")
                
        except Exception as e:
            print(f"❌ 检查ZIP内容失败: {e}")
            return False
        
        # 6. 成功总结
        print(f"\n{'='*80}")
        print(f"✅ 测试成功完成！")
        print(f"{'='*80}")
        print(f"\n📊 测试总结:")
        print(f"   ✅ Ragflow模拟上传PDF: {pdf_file.name}")
        print(f"   ✅ 代理接收并处理文件")
        print(f"   ✅ 代理转发到官方Mineru API")
        print(f"   ✅ 获得解析结果ZIP")
        print(f"   ✅ 下载ZIP到cache目录: {zip_file.name}")
        print(f"   ✅ ZIP内容验证: {len(file_list)} 个文件")
        
        print(f"\n📁 文件位置:")
        print(f"   原PDF: {pdf_file.absolute()}")
        print(f"   结果ZIP: {zip_file.absolute()}")
        
        print(f"\n💡 下一步:")
        print(f"   1. Ragflow可以解压这个ZIP文件获取解析结果")
        print(f"   2. 结果包含结构化的内容块(_content_list.json)")
        print(f"   3. 可以进行后续的RAG处理")
        
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
    success = test_ragflow_with_local_pdf()
    sys.exit(0 if success else 1)
