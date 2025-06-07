import json
from pathlib import Path
from typing import Any, Dict

class Config:
    """配置管理类"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # 加载各模块配置
        self.main_config = self._load_config("config.json")
        self.legal_config = self._load_config("legal_config.json")
        self.api_config = self._load_config("api_config.json")
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = self.config_dir / filename
        if not config_path.exists():
            return {}
        
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_config(self, filename: str, config: Dict[str, Any]) -> None:
        """保存配置到文件"""
        config_path = self.config_dir / filename
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    @property
    def analysis_config(self) -> Dict[str, Any]:
        """获取分析模块配置"""
        return self.main_config.get("analysis", {})
    
    @property
    def legal_analysis_config(self) -> Dict[str, Any]:
        """获取法律分析配置"""
        return self.legal_config
    
    @property
    def api_keys(self) -> Dict[str, str]:
        """获取API密钥配置"""
        return self.api_config.get("api_keys", {})
