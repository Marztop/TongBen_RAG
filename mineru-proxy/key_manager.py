"""API 密钥管理模块"""
import json
import os
from typing import Optional
from logger import logger

KEY_FILE = "keys.json"

def ensure_key_file():
    """确保 keys.json 文件存在"""
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'w') as f:
            json.dump({"mineru_api_key": None}, f, indent=2)

def get_api_key() -> Optional[str]:
    """获取 Mineru API key"""
    ensure_key_file()
    try:
        with open(KEY_FILE, 'r') as f:
            data = json.load(f)
            return data.get("mineru_api_key")
    except Exception as e:
        logger.log_error(e, "get_api_key")
        return None

def set_api_key(key: str) -> bool:
    """设置 Mineru API key"""
    ensure_key_file()
    try:
        with open(KEY_FILE, 'w') as f:
            json.dump({"mineru_api_key": key}, f, indent=2)
        logger.log_info("API key 已更新")
        return True
    except Exception as e:
        logger.log_error(e, "set_api_key")
        return False

def delete_api_key() -> bool:
    """删除 API key"""
    ensure_key_file()
    try:
        with open(KEY_FILE, 'w') as f:
            json.dump({"mineru_api_key": None}, f, indent=2)
        logger.log_info("API key 已删除")
        return True
    except Exception as e:
        logger.log_error(e, "delete_api_key")
        return False

def has_api_key() -> bool:
    """检查是否已设置 API key"""
    key = get_api_key()
    return key is not None and key.strip() != ""
