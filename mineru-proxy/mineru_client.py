import requests
import time
from typing import Dict, Optional, List, Any, Tuple
from config import Config
from logger import logger

class MineruClient:
    """Mineru 官方API客户端"""
    
    def __init__(self):
        self.api_url = Config.MINERU_API_URL
        self.timeout = Config.REQUEST_TIMEOUT
    
    def _get_api_key(self) -> str:
        """获取当前 API key（支持动态更新）"""
        from key_manager import get_api_key
        key = get_api_key()
        if not key:
            key = Config.MINERU_API_KEY
        return key
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        api_key = self._get_api_key()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """发送请求"""
        url = f"{self.api_url}{endpoint}"
        
        if "headers" not in kwargs:
            kwargs["headers"] = self._get_headers()
        else:
            kwargs["headers"].update(self._get_headers())
        
        kwargs["timeout"] = self.timeout
        
        # 记录完整的请求信息
        logger.log_request(method, url, kwargs.get("headers"), kwargs.get("json"))
        
        start_time = time.time()
        try:
            response = requests.request(method, url, **kwargs)
            elapsed = time.time() - start_time
            
            # 记录完整的响应信息（包括响应体）
            response_body = response.text
            logger.log_response(response.status_code, response_body, elapsed)
            
            # 如果是 JSON 响应，也记录解析后的数据
            if response_body:
                try:
                    response_data = response.json()
                    logger.log_api_response(endpoint, response_data, response.status_code)
                except:
                    pass
            
            response.raise_for_status()
            return response.json() if response.text else {}
        except Exception as e:
            logger.log_error(e, f"{method} {endpoint}")
            raise
    
    # === 精准解析 API v4 ===
    
    def create_extract_task(self, url: str, model_version: str = "vlm", **options) -> str:
        """创建单文件解析任务"""
        payload = {
            "url": url,
            "version": model_version,
            **options
        }
        result = self._request("POST", "/api/v4/extract/task", json=payload)
        return result["data"]["task_id"]
    
    def get_extract_task(self, task_id: str) -> Dict:
        """查询单个解析任务结果"""
        result = self._request("GET", f"/api/v4/extract/task/{task_id}")
        return result["data"]
    
    def request_batch_upload_urls(self, files: List[Dict], model_version: str = "vlm", **options) -> Tuple[str, List[str]]:
        """申请批量上传URL"""
        payload = {
            "files": files,
            "version": model_version,
            **options
        }
        result = self._request("POST", "/api/v4/file-urls/batch", json=payload)
        
        # 检查响应格式
        if result.get("code", 0) != 0:
            raise Exception(f"API error: {result.get('msg', 'Unknown error')}")
        
        data = result.get("data")
        if not data:
            raise Exception(f"Invalid response from API: {result}")
        
        batch_id = data.get("batch_id")
        file_urls = data.get("file_urls", [])
        
        if not batch_id:
            raise Exception(f"No batch_id in response: {result}")
        if not file_urls:
            raise Exception(f"No file_urls in response: {result}")
        
        return batch_id, file_urls
    
    def get_batch_results(self, batch_id: str) -> Dict:
        """获取批量任务结果"""
        result = self._request("GET", f"/api/v4/extract-results/batch/{batch_id}")
        
        # 检查响应格式
        if result.get("code", 0) != 0:
            raise Exception(f"API error: {result.get('msg', 'Unknown error')}")
        
        data = result.get("data")
        if not data:
            raise Exception(f"Invalid response from API: {result}")
        
        return data
    
    def create_batch_extract_task(self, files: List[Dict], model_version: str = "vlm", **options) -> str:
        """创建批量解析任务（URL方式）"""
        payload = {
            "files": files,
            "version": model_version,
            **options
        }
        result = self._request("POST", "/api/v4/extract/task/batch", json=payload)
        return result["data"]["batch_id"]
    
    def upload_file(self, upload_url: str, file_content: bytes) -> bool:
        """上传文件到预签名URL"""
        try:
            logger.log_info(f"Uploading file to S3: {len(file_content)} bytes")
            response = requests.put(upload_url, data=file_content, timeout=self.timeout)
            logger.log_response(response.status_code, response.text, None)
            response.raise_for_status()
            logger.log_info(f"Upload successful, status: {response.status_code}")
            return True
        except Exception as e:
            logger.log_error(e, "File upload to S3 failed")
            raise
    
    # === Agent 轻量 API v1 ===
    
    def agent_parse_url(self, url: str, **options) -> str:
        """Agent轻量API - URL解析"""
        payload = {"url": url, **options}
        result = self._request("POST", "/api/v1/agent/parse/url", json=payload)
        return result["data"]["task_id"]
    
    def agent_parse_file(self, file_name: str, **options) -> Tuple[str, str]:
        """Agent轻量API - 申请文件上传"""
        payload = {"file_name": file_name, **options}
        result = self._request("POST", "/api/v1/agent/parse/file", json=payload)
        return result["data"]["task_id"], result["data"]["file_url"]
    
    def agent_get_result(self, task_id: str) -> Dict:
        """Agent轻量API - 查询结果"""
        result = self._request("GET", f"/api/v1/agent/parse/{task_id}")
        return result["data"]

client = MineruClient()
