import time
import os
import json
from datetime import datetime
from typing import Optional, Any
from config import Config
from logger import logger

class MemoryCache:
    """内存缓存 + 磁盘持久化实现"""
    
    def __init__(self):
        self.storage = {}
        self.expiry = {}
        self.cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        
        # 创建缓存目录
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.log_info(f"Cache directory: {self.cache_dir}")
    
    def _get_cache_file(self, key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _save_to_disk(self, key: str, value: Any, ttl: int):
        """保存缓存到磁盘"""
        try:
            cache_file = self._get_cache_file(key)
            cache_data = {
                "key": key,
                "value": value,
                "created_at": datetime.now().isoformat(),
                "ttl": ttl,
                "expires_at": datetime.fromtimestamp(time.time() + ttl).isoformat()
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.log_debug(f"Cache saved to disk: {cache_file}")
        except Exception as e:
            logger.log_error(e, f"Failed to save cache to disk: {key}")
    
    def _load_from_disk(self, key: str) -> Optional[Any]:
        """从磁盘加载缓存"""
        try:
            cache_file = self._get_cache_file(key)
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查过期
            expires_at = datetime.fromisoformat(cache_data.get("expires_at", "2000-01-01"))
            if datetime.now() > expires_at:
                os.remove(cache_file)
                logger.log_debug(f"Cache file expired and removed: {cache_file}")
                return None
            
            logger.log_debug(f"Cache loaded from disk: {cache_file}")
            return cache_data.get("value")
        except Exception as e:
            logger.log_error(e, f"Failed to load cache from disk: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存（内存 + 磁盘）"""
        ttl = ttl or Config.CACHE_TTL
        
        # 保存到内存
        self.storage[key] = value
        self.expiry[key] = time.time() + ttl
        
        # 保存到磁盘
        self._save_to_disk(key, value, ttl)
        
        logger.log_info(f"Cache SET: {key} (TTL: {ttl}s, saved to disk)")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存（先查内存，再查磁盘）"""
        # 先查内存缓存
        if key in self.storage:
            # 检查过期
            if time.time() > self.expiry.get(key, 0):
                del self.storage[key]
                del self.expiry[key]
                logger.log_debug(f"Cache EXPIRED: {key}")
            else:
                logger.log_debug(f"Cache HIT (memory): {key}")
                return self.storage[key]
        
        # 再从磁盘加载
        value = self._load_from_disk(key)
        if value is not None:
            # 恢复到内存缓存
            ttl = Config.CACHE_TTL
            self.storage[key] = value
            self.expiry[key] = time.time() + ttl
            logger.log_info(f"Cache HIT (disk): {key}, restored to memory")
            return value
        
        return None
    
    def delete(self, key: str):
        """删除缓存（内存 + 磁盘）"""
        if key in self.storage:
            del self.storage[key]
            del self.expiry[key]
        
        cache_file = self._get_cache_file(key)
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                logger.log_debug(f"Cache file deleted: {cache_file}")
            except Exception as e:
                logger.log_error(e, f"Failed to delete cache file: {cache_file}")
        
        logger.log_debug(f"Cache DELETE: {key}")
    
    def clear(self):
        """清空缓存（内存 + 磁盘）"""
        self.storage.clear()
        self.expiry.clear()
        
        # 清空磁盘缓存文件
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
            logger.log_info("All cache files cleared from disk")
        except Exception as e:
            logger.log_error(e, "Failed to clear cache directory")
        
        logger.log_info("Cache cleared (memory + disk)")
    
    def get_stats(self):
        """获取缓存统计"""
        # 计算磁盘文件数
        disk_count = 0
        try:
            disk_count = len([f for f in os.listdir(self.cache_dir) if f.endswith('.json')])
        except:
            pass
        
        return {
            "total_keys_memory": len(self.storage),
            "total_keys_disk": disk_count,
            "expired_keys": sum(1 for exp in self.expiry.values() if exp < time.time()),
            "cache_dir": self.cache_dir
        }

cache = MemoryCache()
