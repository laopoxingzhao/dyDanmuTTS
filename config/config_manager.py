import json
import os
from typing import Dict, Any

"""
配置管理器
"""

class ConfigManager:
    def __init__(self, config_file_path: str = "config/app_config.json"):
        self.config_file_path = config_file_path
        self.config_data = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件，如果文件不存在则创建默认配置"""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # 如果配置文件损坏，返回默认配置
                return self.get_default_config()
        else:
            # 如果配置文件不存在，创建默认配置
            default_config = self.get_default_config()
            self.save_config(default_config)
            return default_config
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "tts_settings": {
                "tts_enabled": False,
                "enter_tts_enabled": False,
                "enter_tts_templates": [
                    "欢迎{user_name}进入直播间"
                ],
                "follow_tts_enabled": False,
                "follow_tts_templates": [
                    "感谢{user_name}的关注"
                ],
                "gift_tts_enabled": False,
                "gift_tts_templates": [
                    "感谢{user_name}送出的{gift_name}",
                    "{user_name}送出了礼物，感谢支持"
                ],
                "keyword_tts_enabled": False,
                "keyword_reply_templates": {
                    "1": [
                        "你好啊{user_name}",
                        "欢迎来到直播间{user_name}"
                    ],
                    "问题": [
                        "这是一个好问题",
                        "让我想想怎么回答{user_name}"
                    ],
                    "帮助": [
                        "有什么可以帮助你的吗"
                    ]
                },
                "volume": 70,
                "voice": 0,  # 对应下拉框的索引
                "speed": 10   # 对应滑块的值
            },
            "danmu_settings": {
                # 弹幕显示设置，对应checkbox_labels中的键
                "WebcastChatMessage": True,
                "WebcastGiftMessage": True,
                "WebcastLikeMessage": True,
                "WebcastMemberMessage": True,
                "WebcastSocialMessage": True,
                "WebcastFansclubMessage": True,
                "WebcastEmojiChatMessage": True
            }
        }
    
    def save_config(self, config: Dict[str, Any] = None) -> None:
        """保存配置到文件"""
        if config is None:
            config = self.config_data
        
        # 确保目录存在
        config_dir = os.path.dirname(self.config_file_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_config(self, section: str, key: str, default_value=None):
        """获取配置项的值"""
        if section in self.config_data and key in self.config_data[section]:
            return self.config_data[section][key]
        return default_value
    
    def set_config(self, section: str, key: str, value) -> None:
        """设置配置项的值"""
        if section not in self.config_data:
            self.config_data[section] = {}
        self.config_data[section][key] = value
        # 立即保存到文件
        self.save_config()