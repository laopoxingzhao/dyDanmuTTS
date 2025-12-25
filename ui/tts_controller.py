from PyQt5.QtCore import pyqtSignal
from config.config_manager import global_config_manager
from tts.tts_handler import TTSHandler


class TTSController:
    # 定义信号
    add_log_signal = pyqtSignal(str)
    
    def __init__(self):
        # 使用全局配置管理器
        self.config_manager = global_config_manager
        
    def save_enter_templates(self, template_text_widget):
        """保存进入消息模板"""
        templates = [line.strip() for line in template_text_widget.toPlainText().split('\n') if line.strip()]
        if templates:
            app_config = self.config_manager.get_app_config()
            app_config.tts_settings.enter_tts_templates = templates
            self.config_manager.update_from_app_config(app_config)

    def save_follow_templates(self, template_text_widget):
        """保存关注消息模板"""
        templates = [line.strip() for line in template_text_widget.toPlainText().split('\n') if line.strip()]
        if templates:
            app_config = self.config_manager.get_app_config()
            app_config.tts_settings.follow_tts_templates = templates
            self.config_manager.update_from_app_config(app_config)

    def save_gift_templates(self, template_text_widget):
        """保存礼物消息模板"""
        templates = [line.strip() for line in template_text_widget.toPlainText().split('\n') if line.strip()]
        if templates:
            app_config = self.config_manager.get_app_config()
            app_config.tts_settings.gift_tts_templates = templates
            self.config_manager.update_from_app_config(app_config)

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
            app_config = self.config_manager.get_app_config()
            app_config.tts_settings.keyword_reply_templates = keyword_templates
            self.config_manager.update_from_app_config(app_config)

    def update_tts_queue_config(self, key, value):
        """更新TTS队列配置"""
        app_config = self.config_manager.get_app_config()
        tts_queue_settings = app_config.tts_settings.tts_queue_settings
        
        # 更新配置值
        if key == "dedup_time_window":
            tts_queue_settings.dedup_time_window = value
        elif key == "min_interval":
            tts_queue_settings.min_interval = value
        elif key == "max_queue_size":
            tts_queue_settings.max_queue_size = value
        
        # 更新配置并保存
        self.config_manager.update_from_app_config(app_config)
        
        # 通知TTS处理器更新配置
        self.tts_handler.update_config()
