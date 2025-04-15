import os
import json
import base64
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import QMessageBox

class EmailManager:
    def __init__(self):
        # 修改为使用AppData目录存储配置
        appdata_dir = os.getenv('APPDATA')
        if not appdata_dir:
            appdata_dir = os.path.expanduser('~')
        
        self.config_dir = os.path.join(appdata_dir, 'KnowledgeBaseApp')
        self.config_path = os.path.join(self.config_dir, 'email_config.enc')
        self.key_path = os.path.join(self.config_dir, 'email_key.key')
        
        os.makedirs(self.config_dir, exist_ok=True)

    def _generate_key(self):
        """生成加密密钥"""
        key = Fernet.generate_key()
        with open(self.key_path, 'wb') as f:
            f.write(key)
        return key
    
    def _get_key(self):
        """获取加密密钥"""
        if not os.path.exists(self.key_path):
            return self._generate_key()
        with open(self.key_path, 'rb') as f:
            return f.read()
    
    def save_config(self, config):
        """加密保存邮件配置"""
        try:
            key = self._get_key()
            cipher = Fernet(key)
            encrypted = cipher.encrypt(json.dumps(config).encode())
            with open(self.config_path, 'wb') as f:
                f.write(encrypted)
            return True
        except Exception as e:
            QMessageBox.critical(None, "错误", f"保存配置失败: {str(e)}")
            return False
    
    def load_config(self):
        """加载邮件配置"""
        if not os.path.exists(self.config_path):
            return None
        try:
            key = self._get_key()
            cipher = Fernet(key)
            with open(self.config_path, 'rb') as f:
                encrypted = f.read()
                decrypted = cipher.decrypt(encrypted).decode()
                config = json.loads(decrypted)
                
                # 确保配置包含所有必要字段
                required_fields = ['sender_email', 'auth_code', 'smtp_server', 'smtp_port']
                if not all(field in config for field in required_fields):
                    return None
                
                return config
        except Exception as e:
            print(f"加载配置失败: {str(e)}")
            return None