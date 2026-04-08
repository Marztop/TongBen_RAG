#!/usr/bin/env python3
"""
缓存数据查看工具
用于快速查看和管理本地缓存数据
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")

def format_size(bytes_size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f}{unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f}GB"

def list_cache():
    """列出所有缓存文件"""
    if not os.path.exists(CACHE_DIR):
        print(f"❌ 缓存目录不存在: {CACHE_DIR}")
        return
    
    files = sorted(Path(CACHE_DIR).glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not files:
        print("缓存为空")
        return
    
    print(f"\n📂 缓存文件 ({len(files)} 个):\n")
    print(f"{'文件名':<50} {'大小':<8} {'创建时间'}")
    print("-" * 80)
    
    total_size = 0
    for f in files:
        size = f.stat().st_size
        total_size += size
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{f.name:<50} {format_size(size):<8} {mtime}")
    
    print(f"\n总计: {len(files)} 个文件, {format_size(total_size)}")

def view_cache(key):
    """查看缓存内容"""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    
    if not os.path.exists(cache_file):
        print(f"❌ 缓存文件不存在: {cache_file}")
        return
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n📄 {key}.json\n")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")

def search_cache(keyword):
    """搜索缓存"""
    if not os.path.exists(CACHE_DIR):
        print(f"❌ 缓存目录不存在: {CACHE_DIR}")
        return
    
    print(f"\n🔍 搜索包含 '{keyword}' 的缓存...\n")
    found = 0
    
    for f in Path(CACHE_DIR).glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                if keyword.lower() in content.lower():
                    print(f"✓ {f.name}")
                    found += 1
        except:
            pass
    
    if found == 0:
        print("未找到匹配的缓存")
    else:
        print(f"\n找到 {found} 个缓存")

def delete_cache(key):
    """删除缓存"""
    cache_file = os.path.join(CACHE_DIR, f"{key}.json")
    
    if not os.path.exists(cache_file):
        print(f"❌ 缓存文件不存在: {cache_file}")
        return
    
    try:
        os.remove(cache_file)
        print(f"✓ 已删除: {key}.json")
    except Exception as e:
        print(f"❌ 删除失败: {e}")

def clear_all():
    """清空所有缓存"""
    if not os.path.exists(CACHE_DIR):
        print("缓存目录为空")
        return
    
    files = list(Path(CACHE_DIR).glob("*.json"))
    if not files:
        print("缓存为空")
        return
    
    try:
        for f in files:
            os.remove(f)
        print(f"✓ 已清空 {len(files)} 个缓存文件")
    except Exception as e:
        print(f"❌ 清空失败: {e}")

def show_stats():
    """显示缓存统计"""
    if not os.path.exists(CACHE_DIR):
        print(f"❌ 缓存目录不存在: {CACHE_DIR}")
        return
    
    files = list(Path(CACHE_DIR).glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    
    print(f"\n📊 缓存统计:\n")
    print(f"  文件数: {len(files)}")
    print(f"  总大小: {format_size(total_size)}")
    print(f"  存储位置: {CACHE_DIR}\n")
    
    if files:
        oldest = min(files, key=lambda p: p.stat().st_mtime)
        newest = max(files, key=lambda p: p.stat().st_mtime)
        print(f"  最早: {datetime.fromtimestamp(oldest.stat().st_mtime)}")
        print(f"  最新: {datetime.fromtimestamp(newest.stat().st_mtime)}\n")

def main():
    if len(sys.argv) < 2:
        print("""
缓存管理工具 - mineru-proxy

使用方法:
  python cache_manager.py list              # 列出所有缓存
  python cache_manager.py view <key>        # 查看缓存内容
  python cache_manager.py search <keyword>  # 搜索缓存
  python cache_manager.py delete <key>      # 删除指定缓存
  python cache_manager.py clear             # 清空所有缓存
  python cache_manager.py stats             # 显示统计信息

示例:
  python cache_manager.py list
  python cache_manager.py view task_xxx-xxx-xxx
  python cache_manager.py search "done"
  python cache_manager.py delete task_xxx-xxx-xxx
        """)
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "list":
        list_cache()
    elif cmd == "view" and len(sys.argv) > 2:
        view_cache(sys.argv[2])
    elif cmd == "search" and len(sys.argv) > 2:
        search_cache(sys.argv[2])
    elif cmd == "delete" and len(sys.argv) > 2:
        delete_cache(sys.argv[2])
    elif cmd == "clear":
        confirm = input("确定要清空所有缓存吗? (y/n): ")
        if confirm.lower() == 'y':
            clear_all()
    elif cmd == "stats":
        show_stats()
    else:
        print(f"❌ 未知命令: {cmd}")

if __name__ == "__main__":
    main()
