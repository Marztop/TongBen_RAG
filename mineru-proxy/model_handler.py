from typing import List, Dict
from config import Config
from logger import logger

class ModelHandler:
    """模型版本管理"""
    
    VALID_MODELS = ["pipeline", "vlm", "MinerU-HTML"]
    DEFAULT_MODEL = "vlm"
    
    # Ragflow 后端类型映射到官方 API 模型类型
    RAGFLOW_BACKEND_MAPPING = {
        "pipeline": "pipeline",
        "vlm-http-client": "MinerU-HTML",
        "vlm-transformers": "vlm",
        "vlm-vllm-engine": "vlm",
        "vlm-mlx-engine": "vlm",
        "vlm-vllm-async-engine": "vlm",
        "vlm-lmdeploy-engine": "vlm",
    }
    
    def __init__(self):
        self.default_model = Config.DEFAULT_MODEL if hasattr(Config, 'DEFAULT_MODEL') else self.DEFAULT_MODEL
        self.model_stats = {model: 0 for model in self.VALID_MODELS}
    
    def validate_model(self, model_version: str) -> str:
        """验证并返回model_version，支持 Ragflow 后端类型映射"""
        if not model_version:
            model_version = self.default_model
        
        # 如果是 Ragflow 后端类型，进行映射
        if model_version in self.RAGFLOW_BACKEND_MAPPING:
            mapped_model = self.RAGFLOW_BACKEND_MAPPING[model_version]
            logger.log_info(f"Mapping Ragflow backend '{model_version}' to model '{mapped_model}'")
            model_version = mapped_model
        
        if model_version not in self.VALID_MODELS:
            logger.log_error(
                f"Invalid model: {model_version}. Valid: {self.VALID_MODELS}",
                "Model validation"
            )
            raise ValueError(f"Invalid model_version: {model_version}")
        
        self.model_stats[model_version] += 1
        logger.log_info(f"Using model: {model_version}")
        return model_version
    
    def get_stats(self) -> Dict:
        """获取模型使用统计"""
        return {
            "default_model": self.default_model,
            "stats": self.model_stats
        }

handler = ModelHandler()
