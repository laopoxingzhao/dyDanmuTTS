import json
from pathlib import Path
from typing import Dict
from dataclasses import dataclass, asdict


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
    WebcastRoomStatsMessage: bool = True
    WebcastRoomUserSeqMessage: bool = True
    WebcastRoomMessage: bool = True
    WebcastRoomRankMessage: bool = True
    WebcastRoomStreamAdaptationMessage: bool = True


@dataclass
class TTSSettings:
    """TTS语音合成设置"""
    enabled: bool = True
    voice: str = '晓晓'
    rate: str = '+0%'
    volume: str = '+0%'
    playback_volume: int = 80
    play_interval: float = 0.5
    max_queue_size: int = 30
    cache_dir: str = 'output/cache'
    cache_max_age: int = 86400
    cache_max_size_mb: int = 500
    enable_cache: bool = True
    event_announcement: dict = None
    keyword_rules: dict = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.event_announcement is None:
            self.event_announcement = {}
        if self.keyword_rules is None:
            self.keyword_rules = {}


class LiveConfig:
    """简单的配置管理器"""
    
    def __init__(self, config_file: str = "config/app_config.json"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.danmu_settings = DanmuSettings()
        self.tts_settings = TTSSettings()
        
        # 配置变更回调函数列表
        self._config_change_callbacks = []
        
        # 加载现有配置或创建默认配置
        self.load()
    
    def load(self) -> bool:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 更新弹幕设置
                danmu_data = data.get("danmu_settings", {})
                for key, value in danmu_data.items():
                    if hasattr(self.danmu_settings, key):
                        setattr(self.danmu_settings, key, value)
                
                # 更新TTS设置
                tts_data = data.get("tts_settings", {})
                for key, value in tts_data.items():
                    if hasattr(self.tts_settings, key):
                        setattr(self.tts_settings, key, value)
                
                print(f"配置已从 {self.config_file} 加载")
                return True
            else:
                print(f"配置文件不存在，使用默认配置")
                self.save()  # 保存默认配置
                return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            config_data = {
                "danmu_settings": asdict(self.danmu_settings),
                "tts_settings": asdict(self.tts_settings)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def update_danmu_setting(self, key: str, value) -> bool:
        """更新弹幕设置并自动保存"""
        if hasattr(self.danmu_settings, key):
            setattr(self.danmu_settings, key, value)
            success = self.save()
            if success:
                self._notify_config_change('danmu', key, value)
            return success
        return False
    
    def update_tts_setting(self, key: str, value) -> bool:
        """更新TTS设置并自动保存"""
        if hasattr(self.tts_settings, key):
            setattr(self.tts_settings, key, value)
            success = self.save()
            if success:
                self._notify_config_change('tts', key, value)
            return success
        return False
    
    def add_keyword_rule(self, keyword: str, rule: dict) -> bool:
        """添加关键词规则"""
        self.tts_settings.keyword_rules[keyword] = rule
        return self.save()
    
    def remove_keyword_rule(self, keyword: str) -> bool:
        """移除关键词规则"""
        if keyword in self.tts_settings.keyword_rules:
            del self.tts_settings.keyword_rules[keyword]
            return self.save()
        return False
    
    def update_keyword_rule(self, keyword: str, rule: dict) -> bool:
        """更新关键词规则"""
        if keyword in self.tts_settings.keyword_rules:
            self.tts_settings.keyword_rules[keyword] = rule
            return self.save()
        return False
    
    def add_config_change_callback(self, callback):
        """添加配置变更回调函数"""
        if callback not in self._config_change_callbacks:
            self._config_change_callbacks.append(callback)
            
    def remove_config_change_callback(self, callback):
        """移除配置变更回调函数"""
        if callback in self._config_change_callbacks:
            self._config_change_callbacks.remove(callback)
            
    def _notify_config_change(self, config_type: str, key: str, value):
        """通知配置变更"""
        try:
            for callback in self._config_change_callbacks:
                try:
                    callback(config_type, key, value)
                except Exception as e:
                    print(f"配置变更回调执行失败: {e}")
        except Exception as e:
            print(f"通知配置变更失败: {e}")
            
    def __str__(self) -> str:
        """转换为可读字符串"""
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "danmu_settings": asdict(self.danmu_settings),
            "tts_settings": asdict(self.tts_settings)
        }
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


config_manager = LiveConfig()

# 使用示例
if __name__ == "__main__":
    # 1. 创建配置管理器
    config = LiveConfig("my_config.json")
    
    # 2. 修改弹幕设置
    config.update_danmu_setting("WebcastLikeMessage", False)
    
    # 3. 查看完整配置
    print("\n当前完整配置:")
    print(config)
    
    # 4. 重新加载配置（例如在其他地方修改了文件）
    print("\n重新加载配置...")
    config.load()
    
    # 5. 使用不同路径的配置文件
    print("\n使用不同路径的配置文件...")
    config2 = LiveConfig("another_config.json")
    config2.update_danmu_setting("WebcastLikeMessage", True)
    
    # 6. 创建默认配置（用于新程序）
    default_config = LiveConfig("default_config.json")
    # 首次运行会自动创建带有默认值的配置文件