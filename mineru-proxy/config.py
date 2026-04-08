import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """基础配置"""
    MINERU_API_KEY = os.getenv("MINERU_API_KEY", "")
    MINERU_API_URL = os.getenv("MINERU_API_URL", "https://mineru.net")
    PROXY_PORT = int(os.getenv("PROXY_PORT", 5000))
    PROXY_HOST = os.getenv("PROXY_HOST", "0.0.0.0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 缓存配置
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1小时
    CACHE_DIR = os.getenv("CACHE_DIR", "/app/cache")  # 缓存目录
    
    # 大文件分片配置
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    MAX_PAGES = 600
    CHUNK_SIZE = 100 * 1024 * 1024  # 100MB per chunk
    MAX_PAGES_PER_CHUNK = 300
    
    # 请求配置
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    
    # 临时文件目录
    TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/mineru_proxy")
    
    # 默认模型
    DEFAULT_MODEL = "vlm"
    
    @classmethod
    def validate(cls):
        """验证必需的配置"""
        # MINERU_API_KEY 可以在启动时不设置，可以通过 /key/ 管理界面设置
        # 从 key_manager.get_api_key() 获取，如果没有则使用环境变量
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
