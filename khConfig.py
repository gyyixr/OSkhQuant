# coding: utf-8
import json
from typing import Dict, List, Optional, Any
import time
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os

class KhConfig:
    """配置管理类 - 支持多市场配置"""
    
    # 加密密钥(实际使用时应从环境变量或密钥文件读取)
    _ENCRYPTION_KEY = None
    
    def __init__(self, config_path: str):
        """初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path  # 保存配置文件路径
        # 加载配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config_dict = json.load(f)
        
        # === 多市场配置 ===
        market_config = self.config_dict.get("market", {})
        self.market_type = market_config.get("type", "china_a_stock")  # 默认A股
        self.market_name = market_config.get("name", "A股市场")
        
        # 数据源配置
        data_source_config = self.config_dict.get("data_source", {})
        self.data_provider = data_source_config.get("provider", "miniQMT")
        self.api_key = data_source_config.get("api_key", "")
        self.api_secret = data_source_config.get("api_secret", "")
        self.api_endpoint = data_source_config.get("endpoint", "")
        
        # API凭证(加密存储)
        self.api_credentials = self._load_credentials(data_source_config)
        
        # === 原有配置(保持向后兼容) ===
        # 从根级别或system配置中读取run_mode
        self.run_mode = self.config_dict.get("run_mode") or \
                       self.config_dict.get("system", {}).get("run_mode", "backtest")
        self.userdata_path = self.config_dict.get("system", {}).get("userdata_path", "")
        self.session_id = self.config_dict.get("system", {}).get("session_id", int(time.time()))
        self.check_interval = self.config_dict.get("system", {}).get("check_interval", 3)
        
        # 账户配置，设置默认值
        account_config = self.config_dict.get("account", {})
        self.account_id = account_config.get("account_id", "test_account")
        self.account_type = account_config.get("account_type", "SECURITY_ACCOUNT")
        
        # 回测配置，设置默认值
        backtest_config = self.config_dict.get("backtest", {})
        self.backtest_start = backtest_config.get("start_time", "20240101")
        self.backtest_end = backtest_config.get("end_time", "20241231")
        
        # 从回测配置中获取初始资金
        self.init_capital = backtest_config.get("init_capital", 1000000)
        
        # 数据配置，设置默认值
        data_config = self.config_dict.get("data", {})
        self.kline_period = data_config.get("kline_period", "1d")
        # 优先从stock_list读取，如果没有则使用stock_pool（兼容性）
        self.stock_pool = data_config.get("stock_list", data_config.get("stock_pool", []))
        
        # 风控配置，设置默认值
        risk_config = self.config_dict.get("risk", {})
        self.position_limit = risk_config.get("position_limit", 0.95)
        self.order_limit = risk_config.get("order_limit", 100)
        self.loss_limit = risk_config.get("loss_limit", 0.1)
        
    @property
    def initial_cash(self):
        """获取初始资金，确保与回测配置中的init_capital保持一致"""
        return self.init_capital

    def get_stock_list(self):
        """获取股票列表"""
        data_config = self.config_dict.get("data", {})
        # 优先从stock_list读取，如果没有则使用stock_pool（兼容性）
        return data_config.get("stock_list", data_config.get("stock_pool", []))
    
    def update_stock_list(self, stock_list: List[str]):
        """更新股票列表
        
        Args:
            stock_list: 股票代码列表
        """
        if "data" not in self.config_dict:
            self.config_dict["data"] = {}
        
        # 将股票列表存储到data.stock_list字段
        self.config_dict["data"]["stock_list"] = stock_list
        # 同时更新内存中的stock_pool以保持兼容性
        self.stock_pool = stock_list
        
        # 移除旧的stock_list_file字段（如果存在）
        if "stock_list_file" in self.config_dict["data"]:
            del self.config_dict["data"]["stock_list_file"]

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"加载配置文件失败: {str(e)}")
            
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8", ensure_ascii=False) as f:
                json.dump(self.config_dict, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"保存配置文件失败: {str(e)}")
            
    def update_config(self, key: str, value: Any):
        """更新配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config_dict[key] = value
        self.save_config()
    
    # ==================== 多市场配置方法 ====================
    
    def get_market_type(self) -> str:
        """获取市场类型"""
        return self.market_type
    
    def get_data_provider(self) -> str:
        """获取数据提供商"""
        return self.data_provider
    
    def get_adapter_config(self) -> Dict[str, Any]:
        """获取适配器配置
        
        Returns:
            dict: 适配器需要的配置信息
        """
        config = {
            'market_type': self.market_type,
            'data_provider': self.data_provider,
        }
        
        # A股配置
        if self.market_type == 'china_a_stock':
            config['userdata_path'] = self.userdata_path
            config['client_path'] = self.config_dict.get('system', {}).get('client_path', '')
        
        # 其他市场配置
        else:
            config['api_key'] = self.api_key
            config['api_secret'] = self.api_secret
            config['endpoint'] = self.api_endpoint
            
            # 如果有加密凭证,使用解密后的
            if self.api_credentials:
                config.update(self.api_credentials)
        
        return config
    
    def validate_market_config(self) -> tuple[bool, str]:
        """验证市场配置
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        # 验证市场类型
        valid_markets = ['china_a_stock', 'us_stock', 'hk_stock', 'cryptocurrency']
        if self.market_type not in valid_markets:
            return False, f"无效的市场类型: {self.market_type}"
        
        # A股配置验证
        if self.market_type == 'china_a_stock':
            if not self.userdata_path:
                return False, "A股市场需要配置 userdata_path"
        
        # 其他市场配置验证
        else:
            if not self.data_provider:
                return False, f"{self.market_name}需要配置 data_provider"
            
            # 验证API凭证(非必需,取决于数据源)
            # if not self.api_key or not self.api_secret:
            #     return False, f"{self.market_name}需要配置API凭证"
        
        return True, ""
    
    def _load_credentials(self, data_source_config: Dict) -> Dict[str, str]:
        """加载API凭证(如果加密)
        
        Args:
            data_source_config: 数据源配置
            
        Returns:
            dict: 解密后的凭证
        """
        credentials = {}
        
        # 如果有加密的凭证
        encrypted_credentials = data_source_config.get('encrypted_credentials', '')
        if encrypted_credentials and self._ENCRYPTION_KEY:
            try:
                credentials = self.decrypt_credentials(encrypted_credentials)
            except Exception as e:
                print(f"警告: 解密API凭证失败: {e}")
        
        return credentials
    
    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """获取或生成加密密钥
        
        Returns:
            bytes: 加密密钥
        """
        if cls._ENCRYPTION_KEY is None:
            # 从环境变量读取
            key_str = os.environ.get('KHQUANT_ENCRYPTION_KEY')
            if key_str:
                cls._ENCRYPTION_KEY = key_str.encode()
            else:
                # 生成新密钥(仅用于开发,生产环境应使用环境变量)
                cls._ENCRYPTION_KEY = Fernet.generate_key()
                print("警告: 使用临时生成的加密密钥,生产环境请设置 KHQUANT_ENCRYPTION_KEY 环境变量")
        
        return cls._ENCRYPTION_KEY
    
    def encrypt_credentials(self, credentials: Dict[str, str]) -> str:
        """加密API凭证
        
        Args:
            credentials: 凭证字典 {key: value}
            
        Returns:
            str: 加密后的字符串
        """
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            
            # 将凭证转为JSON字符串
            credentials_json = json.dumps(credentials)
            
            # 加密
            encrypted = fernet.encrypt(credentials_json.encode())
            
            # 转为base64字符串
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            raise Exception(f"加密凭证失败: {str(e)}")
    
    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, str]:
        """解密API凭证
        
        Args:
            encrypted_str: 加密的字符串
            
        Returns:
            dict: 解密后的凭证字典
        """
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            
            # 从base64解码
            encrypted = base64.b64decode(encrypted_str.encode())
            
            # 解密
            decrypted = fernet.decrypt(encrypted)
            
            # 解析JSON
            return json.loads(decrypted.decode())
            
        except Exception as e:
            raise Exception(f"解密凭证失败: {str(e)}")
    
    def save_encrypted_credentials(self, credentials: Dict[str, str]):
        """保存加密的API凭证到配置文件
        
        Args:
            credentials: 凭证字典
        """
        # 加密凭证
        encrypted = self.encrypt_credentials(credentials)
        
        # 更新配置
        if "data_source" not in self.config_dict:
            self.config_dict["data_source"] = {}
        
        self.config_dict["data_source"]["encrypted_credentials"] = encrypted
        
        # 移除明文凭证(安全考虑)
        self.config_dict["data_source"].pop("api_key", None)
        self.config_dict["data_source"].pop("api_secret", None)
        
        # 保存配置
        self.save_config()
        
        print("✓ API凭证已加密保存") 