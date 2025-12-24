from PyQt5.QtCore import Qt
from config.config_manager import ConfigManager
from tool.myqueue import ttsq
from collections import deque

class TTSController:
    def __init__(self):
        self.config_manager = ConfigManager()
        
    def save_enter_templates(self, template_text_widget):
        """保存进入消息模板"""
        templates = [line.strip() for line in template_text_widget.toPlainText().split('\n') if line.strip()]
        if templates:
            self.config_manager.set_config("tts_settings", "enter_tts_templates", templates)

    def save_follow_templates(self, template_text_widget):
        """保存关注消息模板"""
        templates = [line.strip() for line in template_text_widget.toPlainText().split('\n') if line.strip()]
        if templates:
            self.config_manager.set_config("tts_settings", "follow_tts_templates", templates)

    def save_gift_templates(self, template_text_widget):
        """保存礼物消息模板"""
        templates = [line.strip() for line in template_text_widget.toPlainText().split('\n') if line.strip()]
        if templates:
            self.config_manager.set_config("tts_settings", "gift_tts_templates", templates)

    def save_keyword_templates(self, template_text_widget):
        """保存关键字回复模板"""
        lines = template_text_widget.toPlainText().split('\n')
        keyword_templates = {}
        for line in lines:
            line = line.strip()
            if line and '=' in line:
                parts = line.split('=', 1)  # 只分割第一个等号
                keyword = parts[0].strip()
                templates_str = parts[1].strip()
                templates = [t.strip() for t in templates_str.split('|') if t.strip()]
                if keyword and templates:
                    keyword_templates[keyword] = templates
        if keyword_templates:
            self.config_manager.set_config("tts_settings", "keyword_reply_templates", keyword_templates)

    def update_tts_queue_config(self, key, value):
        """更新TTS队列配置"""
        tts_queue_settings = self.config_manager.get_config("tts_settings", "tts_queue_settings", {})
        tts_queue_settings[key] = value
        self.config_manager.set_config("tts_settings", "tts_queue_settings", tts_queue_settings)
        
        # 更新全局TTS队列配置
        if key == "dedup_time_window":
            ttsq.dedup_time_window = value
        elif key == "min_interval":
            ttsq.min_interval = value
        elif key == "max_queue_size":
            ttsq.max_queue_size = value
            ttsq.recent_messages = deque(maxlen=value)  # 更新最近消息队列长度