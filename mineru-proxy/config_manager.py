import json
import os
from pathlib import Path
from logger import logger

class ConfigManager:
    """配置管理器 - 管理 API Key 和 PDF 分片配置"""
    
    CONFIG_FILE = "config.json"
    
    DEFAULT_CONFIG = {
        "api_key": "",
        "pdf_chunking": {
            "enabled": True,
            "max_file_size": 200 * 1024 * 1024,  # 200MB
            "max_pages": 600,
            "chunk_size": 100 * 1024 * 1024,  # 100MB per chunk
            "max_pages_per_chunk": 300
        }
    }
    
    @classmethod
    def load_config(cls):
        """加载配置文件"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.log_info(f"Loaded config from {cls.CONFIG_FILE}")
                return config
            except Exception as e:
                logger.log_error(e, "load_config")
        return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def save_config(cls, config: dict):
        """保存配置文件"""
        try:
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.log_info(f"Saved config to {cls.CONFIG_FILE}")
            return True
        except Exception as e:
            logger.log_error(e, "save_config")
            return False
    
    @classmethod
    def get_api_key(cls):
        """获取 API Key"""
        config = cls.load_config()
        return config.get("api_key", "")
    
    @classmethod
    def set_api_key(cls, key: str):
        """保存 API Key"""
        config = cls.load_config()
        config["api_key"] = key.strip()
        return cls.save_config(config)
    
    @classmethod
    def delete_api_key(cls):
        """删除 API Key"""
        config = cls.load_config()
        config["api_key"] = ""
        return cls.save_config(config)
    
    @classmethod
    def has_api_key(cls):
        """检查是否有 API Key"""
        return bool(cls.get_api_key())
    
    @classmethod
    def get_chunking_config(cls):
        """获取分片配置"""
        config = cls.load_config()
        return config.get("pdf_chunking", cls.DEFAULT_CONFIG["pdf_chunking"])
    
    @classmethod
    def set_chunking_config(cls, chunking_config: dict):
        """保存分片配置"""
        config = cls.load_config()
        
        # 验证和更新配置
        pdf_chunking = config.get("pdf_chunking", {})
        
        if "enabled" in chunking_config:
            pdf_chunking["enabled"] = bool(chunking_config["enabled"])
        
        if "max_file_size" in chunking_config:
            pdf_chunking["max_file_size"] = int(chunking_config["max_file_size"])
        
        if "max_pages" in chunking_config:
            pdf_chunking["max_pages"] = int(chunking_config["max_pages"])
        
        if "chunk_size" in chunking_config:
            pdf_chunking["chunk_size"] = int(chunking_config["chunk_size"])
        
        if "max_pages_per_chunk" in chunking_config:
            pdf_chunking["max_pages_per_chunk"] = int(chunking_config["max_pages_per_chunk"])
        
        config["pdf_chunking"] = pdf_chunking
        return cls.save_config(config)
    
    @classmethod
    def get_all_config(cls):
        """获取所有配置（不包含敏感信息）"""
        config = cls.load_config()
        return {
            "api_key": config.get("api_key", ""),
            "has_api_key": bool(config.get("api_key", "")),
            "pdf_chunking": config.get("pdf_chunking", cls.DEFAULT_CONFIG["pdf_chunking"])
        }
