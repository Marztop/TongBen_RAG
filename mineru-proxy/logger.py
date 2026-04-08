import logging
import json
import traceback
import os
from datetime import datetime
from config import Config

class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(Config.LOG_LEVEL)
        self.logger.handlers = []  # 清除已有的处理器
        
        # 创建日志目录
        os.makedirs("logs", exist_ok=True)
        
        # 控制台输出
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件输出
        log_file = f"logs/mineru_proxy_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _format_body(self, body, max_len=1000):
        """格式化请求/响应体"""
        if body is None:
            return "(empty)"
        
        if isinstance(body, bytes):
            try:
                body_str = body.decode('utf-8', errors='ignore')
            except:
                body_str = f"(binary: {len(body)} bytes)"
        else:
            body_str = str(body)
        
        if len(body_str) > max_len:
            return body_str[:max_len] + f"... (total {len(body_str)} chars)"
        return body_str
    
    def log_request(self, method, url, headers, body=None):
        """记录请求 - 包括完整的请求体"""
        msg = f"\n{'='*60}\n📤 REQUEST: {method} {url}\n"
        msg += f"Headers: {json.dumps(headers, ensure_ascii=False)}\n"
        if body:
            msg += f"Body: {self._format_body(body)}\n"
        msg += f"{'='*60}"
        self.logger.info(msg)
    
    def log_response(self, status_code, response_body=None, elapsed_time=None):
        """记录响应 - 包括完整的响应体"""
        msg = f"\n{'='*60}\n📥 RESPONSE: {status_code}\n"
        if response_body:
            msg += f"Body: {self._format_body(response_body, max_len=2000)}\n"
        if elapsed_time:
            msg += f"Time: {elapsed_time:.2f}s\n"
        msg += f"{'='*60}"
        self.logger.info(msg)
    
    def log_error(self, error, context=""):
        """记录错误 - 包括完整的堆栈跟踪"""
        msg = f"\n{'='*60}\n❌ ERROR in {context}\n"
        msg += f"Message: {str(error)}\n"
        msg += f"Traceback:\n{traceback.format_exc()}"
        msg += f"{'='*60}"
        self.logger.error(msg)
    
    def log_info(self, message):
        """记录信息"""
        self.logger.info(f"ℹ️  {message}")
    
    def log_debug(self, message):
        """记录调试信息"""
        self.logger.debug(f"🐛 {message}")
    
    def log_ragflow_request(self, file_name, file_size, backend, form_data):
        """记录 Ragflow 请求"""
        msg = f"\n{'='*60}\n🔍 RAGFLOW REQUEST RECEIVED\n"
        msg += f"File: {file_name}\n"
        msg += f"Size: {file_size} bytes\n"
        msg += f"Backend: {backend}\n"
        msg += f"Form Data: {json.dumps(form_data, ensure_ascii=False)}\n"
        msg += f"{'='*60}"
        self.logger.info(msg)
    
    def log_api_response(self, endpoint, response_data, status_code=None):
        """记录 API 响应数据"""
        msg = f"\n{'='*60}\n📊 API RESPONSE\n"
        msg += f"Endpoint: {endpoint}\n"
        if status_code:
            msg += f"Status: {status_code}\n"
        msg += f"Data: {json.dumps(response_data, ensure_ascii=False)[:2000]}\n"
        msg += f"{'='*60}"
        self.logger.info(msg)

logger = StructuredLogger(__name__)
