import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class TTSSettings:
    """TTS相关设置"""
    tts_enabled: bool = True
    enter_tts_enabled: bool = False
    enter_tts_templates: List[str] = field(default_factory=lambda: ["欢迎{user_name}进入直播间"])
    follow_tts_enabled: bool = False
    follow_tts_templates: List[str] = field(default_factory=lambda: ["感谢{user_name}的关注"])
    gift_tts_enabled: bool = False
    gift_tts_templates: List[str] = field(default_factory=lambda: [
        "感谢{user_name}送出的{gift_name}",
        "{user_name}送出了礼物，感谢支持"
    ])
    keyword_tts_enabled: bool = False
    keyword_reply_templates: Dict[str, List[str]] = field(default_factory=lambda: {
        "1": ["你好啊{user_name}", "欢迎来到直播间{user_name}"],
        "问题": ["这是一个好问题", "让我想想怎么回答{user_name}"],
        "帮助": ["有什么可以帮助你的吗"]
    })
    volume: int = 70
    voice: int = 0
    speed: int = 10


@dataclass
class DanmuSettings:
    """弹幕消息订阅设置"""
    WebcastChatMessage: bool = True
    WebcastGiftMessage: bool = True
    WebcastLikeMessage: bool = True
    WebcastMemberMessage: bool = True
    WebcastSocialMessage: bool = True
    WebcastFansclubMessage: bool = True
    WebcastEmojiChatMessage: bool = True


class LiveConfig:
    """简单的配置管理器"""
    
    def __init__(self, config_file: str = "config/app_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.tts_settings = TTSSettings()
        self.danmu_settings = DanmuSettings()
        
        # 加载现有配置或创建默认配置
        self.load()
    
    def load(self) -> bool:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 更新TTS设置
                tts_data = data.get("tts_settings", {})
                for key, value in tts_data.items():
                    if hasattr(self.tts_settings, key):
                        setattr(self.tts_settings, key, value)
                
                # 更新弹幕设置
                danmu_data = data.get("danmu_settings", {})
                for key, value in danmu_data.items():
                    if hasattr(self.danmu_settings, key):
                        setattr(self.danmu_settings, key, value)
                
                print(f"✓ 配置已从 {self.config_file} 加载")
                return True
            else:
                print(f"⚠ 配置文件不存在，使用默认配置")
                self.save()  # 保存默认配置
                return True
        except Exception as e:
            print(f"✗ 加载配置失败: {e}")
            return False
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            config_data = {
                "tts_settings": asdict(self.tts_settings),
                "danmu_settings": asdict(self.danmu_settings)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"✗ 保存配置失败: {e}")
            return False
    
    def update_tts_setting(self, key: str, value) -> bool:
        """更新TTS设置并自动保存"""
        if hasattr(self.tts_settings, key):
            setattr(self.tts_settings, key, value)
            return self.save()
        return False
    
    def update_danmu_setting(self, key: str, value) -> bool:
        """更新弹幕设置并自动保存"""
        if hasattr(self.danmu_settings, key):
            setattr(self.danmu_settings, key, value)
            return self.save()
        return False
    
    def add_keyword_reply(self, keyword: str, replies: List[str]) -> bool:
        """添加关键词回复并自动保存"""
        self.tts_settings.keyword_reply_templates[keyword] = replies
        return self.save()
    
    def remove_keyword(self, keyword: str) -> bool:
        """移除关键词回复并自动保存"""
        if keyword in self.tts_settings.keyword_reply_templates:
            del self.tts_settings.keyword_reply_templates[keyword]
            return self.save()
        return False
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "tts_settings": asdict(self.tts_settings),
            "danmu_settings": asdict(self.danmu_settings)
        }
    
    def __str__(self) -> str:
        """转换为可读字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


config_manager = LiveConfig()

# 使用示例
if __name__ == "__main__":
    # 1. 创建配置管理器
    config = LiveConfig("my_config.json")
    
    # 2. 访问配置
    print(f"当前音量: {config.tts_settings.volume}")
    print(f"是否启用TTS: {config.tts_settings.tts_enabled}")
    print(f"关键词列表: {list(config.tts_settings.keyword_reply_templates.keys())}")
    
    # 3. 修改配置并自动保存
    print("\n修改配置...")
    config.update_tts_setting("volume", 80)  # 修改音量并保存
    config.update_tts_setting("speed", 12)   # 修改语速并保存
    
    # 4. 添加新的关键词回复
    config.add_keyword_reply("谢谢", ["感谢{user_name}的支持", "不用客气"])
    
    # 5. 修改弹幕设置
    config.update_danmu_setting("WebcastLikeMessage", False)
    
    # 6. 查看完整配置
    print("\n当前完整配置:")
    print(config)
    
    # 7. 重新加载配置（例如在其他地方修改了文件）
    print("\n重新加载配置...")
    config.load()
    print(f"重新加载后的音量: {config.tts_settings.volume}")
    
    # 8. 使用不同路径的配置文件
    print("\n使用不同路径的配置文件...")
    config2 = LiveConfig("another_config.json")
    config2.update_tts_setting("volume", 60)
    
    # 9. 创建默认配置（用于新程序）
    default_config = LiveConfig("default_config.json")
    # 首次运行会自动创建带有默认值的配置文件