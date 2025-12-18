import sys
import threading
import os
import json
import random

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QTextEdit, QLabel, QGroupBox, QCheckBox, QMessageBox,
    QTabWidget, QListWidget, QListWidgetItem, QDialog, QTextBrowser, QFormLayout,
    QTextEdit
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor

from liveMan import DouyinLiveWebFetcher


class TTSConfigDialog(QDialog):
    """TTS配置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TTS配置")
        self.setGeometry(300, 300, 600, 500)
        self.config = {}
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # TTS总开关
        self.tts_enabled = QCheckBox("启用TTS语音播报")
        layout.addWidget(self.tts_enabled)
        
        # 进场消息TTS
        enter_group = QGroupBox("用户进场TTS")
        enter_layout = QVBoxLayout()
        self.enter_tts_enabled = QCheckBox("启用进场TTS播报")
        enter_layout.addWidget(self.enter_tts_enabled)
        
        enter_templates_label = QLabel("播报模板（每行一个，随机选择）:")
        self.enter_tts_templates = QTextEdit()
        self.enter_tts_templates.setMaximumHeight(60)
        self.enter_tts_templates.setPlaceholderText("欢迎 {user_name} 来到直播间\n欢迎 {user_name} 加入我们的直播间")
        enter_layout.addWidget(enter_templates_label)
        enter_layout.addWidget(self.enter_tts_templates)
        enter_group.setLayout(enter_layout)
        layout.addWidget(enter_group)
        
        # 关注消息TTS
        follow_group = QGroupBox("用户关注TTS")
        follow_layout = QVBoxLayout()
        self.follow_tts_enabled = QCheckBox("启用关注TTS播报")
        follow_layout.addWidget(self.follow_tts_enabled)
        
        follow_templates_label = QLabel("播报模板（每行一个，随机选择）:")
        self.follow_tts_templates = QTextEdit()
        self.follow_tts_templates.setMaximumHeight(60)
        self.follow_tts_templates.setPlaceholderText("感谢 {user_name} 的关注\n谢谢 {user_name} 关注我们")
        follow_layout.addWidget(follow_templates_label)
        follow_layout.addWidget(self.follow_tts_templates)
        follow_group.setLayout(follow_layout)
        layout.addWidget(follow_group)
        
        # 礼物消息TTS
        gift_group = QGroupBox("礼物TTS")
        gift_layout = QVBoxLayout()
        self.gift_tts_enabled = QCheckBox("启用礼物TTS播报")
        gift_layout.addWidget(self.gift_tts_enabled)
        
        gift_templates_label = QLabel("播报模板（每行一个，随机选择）:")
        self.gift_tts_templates = QTextEdit()
        self.gift_tts_templates.setMaximumHeight(60)
        self.gift_tts_templates.setPlaceholderText("感谢 {user_name} 送出的 {gift_name} x {gift_count}\n{user_name} 送出了 {gift_name} x {gift_count}，感谢支持")
        gift_layout.addWidget(gift_templates_label)
        gift_layout.addWidget(self.gift_tts_templates)
        gift_group.setLayout(gift_layout)
        layout.addWidget(gift_group)
        
        # 关键字TTS
        keyword_group = QGroupBox("关键字TTS")
        keyword_layout = QVBoxLayout()
        self.keyword_tts_enabled = QCheckBox("启用关键字TTS播报")
        keyword_layout.addWidget(self.keyword_tts_enabled)
        
        # 关键字与回复模板映射说明
        keyword_mapping_desc = QLabel("关键字与回复模板映射（格式：关键字=模板1|模板2|模板3）:")
        keyword_mapping_desc.setWordWrap(True)
        keyword_layout.addWidget(keyword_mapping_desc)
        
        self.keyword_mapping_text = QTextEdit()
        self.keyword_mapping_text.setMaximumHeight(150)
        self.keyword_mapping_text.setPlaceholderText(
            "你好=你好啊 {user_name}|欢迎来到直播间 {user_name}\n"
            "问题=这是一个好问题|让我想想怎么回答 {user_name}\n"
            "帮助=有什么可以帮助你的吗 {user_name}|需要帮助请私信主播"
        )
        keyword_layout.addWidget(self.keyword_mapping_text)
        
        keyword_group.setLayout(keyword_layout)
        layout.addWidget(keyword_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self.save_config)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        
    def load_config(self):
        """加载配置"""
        config_file = "tts_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    
                self.tts_enabled.setChecked(self.config.get('tts_enabled', False))
                self.enter_tts_enabled.setChecked(self.config.get('enter_tts_enabled', False))
                enter_templates = '\n'.join(self.config.get('enter_tts_templates', ['欢迎 {user_name} 来到直播间']))
                self.enter_tts_templates.setPlainText(enter_templates)
                
                self.follow_tts_enabled.setChecked(self.config.get('follow_tts_enabled', False))
                follow_templates = '\n'.join(self.config.get('follow_tts_templates', ['感谢 {user_name} 的关注']))
                self.follow_tts_templates.setPlainText(follow_templates)
                
                self.gift_tts_enabled.setChecked(self.config.get('gift_tts_enabled', False))
                gift_templates = '\n'.join(self.config.get('gift_tts_templates', ['感谢 {user_name} 送出的 {gift_name} x {gift_count}']))
                self.gift_tts_templates.setPlainText(gift_templates)
                
                self.keyword_tts_enabled.setChecked(self.config.get('keyword_tts_enabled', False))
                
                # 加载关键字与回复模板映射
                keyword_mappings = []
                keyword_reply_templates = self.config.get('keyword_reply_templates', {})
                for keyword, templates in keyword_reply_templates.items():
                    mapping_str = f"{keyword}={'|'.join(templates)}"
                    keyword_mappings.append(mapping_str)
                self.keyword_mapping_text.setPlainText('\n'.join(keyword_mappings))
            except Exception as e:
                print(f"加载TTS配置失败: {e}")
                
    def save_config(self):
        """保存配置"""
        self.config = {
            'tts_enabled': self.tts_enabled.isChecked(),
            'enter_tts_enabled': self.enter_tts_enabled.isChecked(),
            'enter_tts_templates': self.enter_tts_templates.toPlainText().split('\n'),
            'follow_tts_enabled': self.follow_tts_enabled.isChecked(),
            'follow_tts_templates': self.follow_tts_templates.toPlainText().split('\n'),
            'gift_tts_enabled': self.gift_tts_enabled.isChecked(),
            'gift_tts_templates': self.gift_tts_templates.toPlainText().split('\n'),
            'keyword_tts_enabled': self.keyword_tts_enabled.isChecked(),
            'keyword_reply_templates': keyword_reply_templates
        }
        
        # 清理空模板
        for key in ['enter_tts_templates', 'follow_tts_templates', 'gift_tts_templates']:
            self.config[key] = [template for template in self.config[key] if template.strip()]
        
        try:
            with open("tts_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存配置失败: {e}")


class WorkerSignals(QObject):
    """工作线程信号类"""
    message_received = pyqtSignal(dict)
    status_update = pyqtSignal(str)


class DanmakuWorker(QObject):
    """弹幕处理工作线程"""
    
    def __init__(self, live_id):
        super().__init__()
        self.live_id = live_id
        self.fetcher = DouyinLiveWebFetcher(live_id)
        self.signals = WorkerSignals()
        self.running = False
        
        # 设置状态更新回调
        self.fetcher.on_status_update = self._on_status_update

    def start_listening(self):
        """开始监听弹幕"""
        self.running = True
        # 在新线程中启动fetcher
        threading.Thread(target=self._run_fetcher, daemon=True).start()
        # 在新线程中处理消息
        threading.Thread(target=self._process_messages, daemon=True).start()

    def stop_listening(self):
        """停止监听弹幕"""
        self.running = False
        self.fetcher.stop()

    def _run_fetcher(self):
        """运行弹幕获取器"""
        try:
            self.signals.status_update.emit("正在连接直播间...")
            self.fetcher.start()
        except Exception as e:
            self.signals.status_update.emit(f"连接错误: {str(e)}")

    def _process_messages(self):
        """处理消息"""
        while self.running:
            try:
                message = self.fetcher.get_message(timeout=1)
                if message:
                    self.signals.message_received.emit(message)
            except Exception as e:
                self.signals.status_update.emit(f"消息处理错误: {str(e)}")
                
    def _on_status_update(self, status):
        """内部状态更新处理"""
        self.signals.status_update.emit(status)


class DouyinLiveGUI(QWidget):
    """抖音直播弹幕获取GUI"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.tts_config = {}
        self.init_ui()
        self.setup_timers()
        self.load_tts_config()
        
    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle('抖音直播弹幕获取器')
        self.setGeometry(200, 200, 1000, 700)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 主控页面板
        main_widget = QWidget()
        main_layout_inner = QVBoxLayout()
        
        # 创建输入区域
        input_group = QGroupBox("直播间设置")
        input_layout = QHBoxLayout()
        
        self.room_label = QLabel("直播间ID:")
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("请输入抖音直播间ID...")
        
        self.start_button = QPushButton("开始监听")
        self.start_button.clicked.connect(self.start_listening)
        
        self.stop_button = QPushButton("停止监听")
        self.stop_button.clicked.connect(self.stop_listening)
        self.stop_button.setEnabled(False)
        
        input_layout.addWidget(self.room_label)
        input_layout.addWidget(self.room_input)
        input_layout.addWidget(self.start_button)
        input_layout.addWidget(self.stop_button)
        
        input_group.setLayout(input_layout)
        
        # 创建状态显示区域
        status_group = QGroupBox("状态信息")
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("状态: 未开始")
        status_layout.addWidget(self.status_label)
        
        status_group.setLayout(status_layout)
        
        # 创建统计信息显示区域
        stats_group = QGroupBox("直播间统计信息")
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("在线人数: --, 累计观看: --")
        stats_layout.addWidget(self.stats_label)
        
        stats_group.setLayout(stats_layout)
        
        # 创建消息类型筛选区域
        filter_group = QGroupBox("消息筛选")
        filter_layout = QVBoxLayout()
        
        # 创建复选框网格布局
        checkbox_layout = QGridLayout()
        
        self.filter_checkboxes = {}
        filter_types = [
            ("聊天", "chat"), ("礼物", "gift"), ("点赞", "like"),
            ("进场", "member"), ("关注", "social"), ("统计", "room_stats"),
            ("粉丝团", "fansclub"), ("控制", "control"), ("表情包", "emoji_chat")
        ]
        
        for i, (label, key) in enumerate(filter_types):
            row = i // 3
            col = i % 3
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)  # 默认全选
            checkbox.stateChanged.connect(self.on_filter_changed)
            self.filter_checkboxes[key] = checkbox
            checkbox_layout.addWidget(checkbox, row, col)
        
        # 全选/取消全选按钮
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("全选")
        self.select_all_button.clicked.connect(self.select_all_filters)
        self.deselect_all_button = QPushButton("取消全选")
        self.deselect_all_button.clicked.connect(self.deselect_all_filters)
        
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.deselect_all_button)
        button_layout.addStretch()
        
        filter_layout.addLayout(checkbox_layout)
        filter_layout.addLayout(button_layout)
        filter_group.setLayout(filter_layout)
        
        # 创建弹幕显示区域
        danmaku_group = QGroupBox("弹幕内容")
        danmaku_layout = QVBoxLayout()
        
        self.danmaku_display = QTextEdit()
        self.danmaku_display.setReadOnly(True)
        
        # 添加清屏按钮
        clear_button = QPushButton("清屏")
        clear_button.clicked.connect(self.clear_display)
        
        danmaku_layout.addWidget(self.danmaku_display)
        danmaku_layout.addWidget(clear_button)
        danmaku_group.setLayout(danmaku_layout)
        
        # 添加组件到主布局
        main_layout_inner.addWidget(input_group)
        main_layout_inner.addWidget(status_group)
        main_layout_inner.addWidget(stats_group)
        main_layout_inner.addWidget(filter_group)
        main_layout_inner.addWidget(danmaku_group)
        main_widget.setLayout(main_layout_inner)
        
        # TTS配置面板
        tts_widget = QWidget()
        tts_layout = QVBoxLayout()
        
        tts_desc = QTextBrowser()
        tts_desc.setHtml("""
        <h3>TTS语音播报配置说明</h3>
        <p><b>功能说明：</b></p>
        <ul>
        <li><b>启用TTS语音播报</b>：开启或关闭所有TTS功能</li>
        <li><b>用户进场TTS</b>：当有用户进入直播间时进行语音播报</li>
        <li><b>用户关注TTS</b>：当有用户关注主播时进行语音播报</li>
        <li><b>礼物TTS</b>：当有用户送礼物时进行语音播报</li>
        <li><b>关键字TTS</b>：当聊天内容包含指定关键字时进行语音播报，并可自定义回复模板</li>
        </ul>
        <p><b>模板变量：</b></p>
        <ul>
        <li>{user_name}：用户名</li>
        <li>{content}：聊天内容</li>
        <li>{gift_name}：礼物名称</li>
        <li>{gift_count}：礼物数量</li>
        </ul>
        <p><b>使用方法：</b></p>
        <ol>
        <li>点击下方"配置TTS"按钮打开配置对话框</li>
        <li>根据需要启用相应的TTS功能</li>
        <li>为每种功能添加多个播报模板（每行一个）</li>
        <li>系统会从启用功能的模板中随机选择一个进行播报</li>
        <li>对于关键字播报，可以添加需要监听的关键词</li>
        <li>保存配置后立即生效</li>
        </ol>
        """)
        
        tts_config_btn = QPushButton("配置TTS")
        tts_config_btn.clicked.connect(self.open_tts_config)
        
        tts_layout.addWidget(tts_desc)
        tts_layout.addWidget(tts_config_btn)
        tts_widget.setLayout(tts_layout)
        
        # 添加标签页
        tab_widget.addTab(main_widget, "主控面板")
        tab_widget.addTab(tts_widget, "TTS配置")
        
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
    
    def setup_timers(self):
        """设置定时器"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        
    def start_listening(self):
        """开始监听"""
        room_id = self.room_input.text().strip()
        if not room_id:
            self.status_label.setText("状态: 请输入直播间ID")
            QMessageBox.warning(self, "警告", "请输入直播间ID")
            return
            
        # 禁用开始按钮，启用停止按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.room_input.setEnabled(False)
        
        # 清空显示区域
        self.danmaku_display.clear()
        
        # 创建并启动工作线程
        self.worker = DanmakuWorker(room_id)
        self.worker.signals.message_received.connect(self.handle_message)
        self.worker.signals.status_update.connect(self.update_status)
        self.worker.start_listening()
        
        self.status_label.setText("状态: 正在连接直播间...")
        
    def stop_listening(self):
        """停止监听"""
        if self.worker:
            self.worker.stop_listening()
            
        # 启用开始按钮，禁用停止按钮
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.room_input.setEnabled(True)
        
        self.status_label.setText("状态: 已停止监听")
        
    def handle_message(self, message):
        """处理接收到的消息"""
        # 根据消息类型格式化显示
        msg_type = message['type']
        payload = message['payload']
        
        # 特殊处理统计信息更新
        if msg_type == 'room_stats':
            current_viewers = payload.get('current_viewers', '--')
            total_viewers = payload.get('total_viewers', '--')
            self.stats_label.setText(f"在线人数: {current_viewers}, 累计观看: {total_viewers}")
        
        # 检查筛选条件
        # 对于未在筛选列表中的消息类型，默认显示
        if msg_type in self.filter_checkboxes and not self.filter_checkboxes[msg_type].isChecked():
            return  # 不符合筛选条件，不显示
        
        display_text = ""
        if msg_type == 'chat':
            display_text = f"[聊天] {payload['user_name']}: {payload['content']}"
            # 检查是否需要TTS播报
            self.check_tts_trigger(msg_type, payload)
        elif msg_type == 'gift':
            display_text = f"[礼物] {payload['user_name']} 送出了 {payload['gift_name']} x{payload['gift_count']}"
            # 检查是否需要TTS播报
            self.check_tts_trigger(msg_type, payload)
        elif msg_type == 'like':
            display_text = f"[点赞] {payload['user_name']} 点了{payload['count']}个赞"
        elif msg_type == 'member':
            display_text = f"[进场] {payload['user_name']} 进入了直播间"
            # 检查是否需要TTS播报
            self.check_tts_trigger(msg_type, payload)
        elif msg_type == 'social':
            display_text = f"[关注] {payload['user_name']} 关注了主播"
            # 检查是否需要TTS播报
            self.check_tts_trigger(msg_type, payload)
        elif msg_type == 'room_stats':
            display_text = f"[统计] 当前观看人数: {payload['current_viewers']}, 累计观看人数: {payload['total_viewers']}"
        elif msg_type == 'fansclub':
            display_text = f"[粉丝团] {payload['content']}"
        elif msg_type == 'control':
            display_text = f"[控制] 直播间状态: {payload['status']}"
        elif msg_type == 'emoji_chat':
            display_text = f"[表情包] {payload['user'].nick_name}: {payload['default_content']}"
        else:
            display_text = f"[{msg_type}] {payload}"
            
        # 添加到显示区域（统计信息除外）
        if msg_type != 'room_stats':
            self.danmaku_display.append(display_text)
        
        # 自动滚动到底部
        self.danmaku_display.moveCursor(QTextCursor.End)
        
    def check_tts_trigger(self, msg_type, payload):
        """检查是否触发TTS播报"""
        # 检查TTS是否启用
        if not self.tts_config.get('tts_enabled', False):
            return
            
        tts_text = ""
        
        # 进场TTS播报
        if msg_type == 'member' and self.tts_config.get('enter_tts_enabled', False):
            templates = self.tts_config.get('enter_tts_templates', ['欢迎 {user_name} 来到直播间'])
            if templates:
                template = random.choice(templates)
                user_name = payload.get('user_name', '')
                tts_text = template.format(user_name=user_name)
            
        # 关注TTS播报
        elif msg_type == 'social' and self.tts_config.get('follow_tts_enabled', False):
            templates = self.tts_config.get('follow_tts_templates', ['感谢 {user_name} 的关注'])
            if templates:
                template = random.choice(templates)
                user_name = payload.get('user_name', '')
                tts_text = template.format(user_name=user_name)
            
        # 礼物TTS播报
        elif msg_type == 'gift' and self.tts_config.get('gift_tts_enabled', False):
            templates = self.tts_config.get('gift_tts_templates', ['感谢 {user_name} 送出的 {gift_name} x {gift_count}'])
            if templates:
                template = random.choice(templates)
                user_name = payload.get('user_name', '')
                gift_name = payload.get('gift_name', '')
                gift_count = payload.get('gift_count', '')
                tts_text = template.format(user_name=user_name, gift_name=gift_name, gift_count=gift_count)
            
        # 关键字TTS播报
        elif msg_type == 'chat' and self.tts_config.get('keyword_tts_enabled', False):
            content = payload.get('content', '')
            user_name = payload.get('user_name', '')
            
            # 查找匹配的关键字和对应的模板
            keyword_reply_templates = self.tts_config.get('keyword_reply_templates', {})
            matched_keyword = None
            matched_templates = []
            
            # 精确匹配关键字
            for keyword, templates in keyword_reply_templates.items():
                if keyword in content:
                    matched_keyword = keyword
                    matched_templates = templates
                    break
            
            # 如果找到匹配的关键字且有对应的模板，则随机选择一个模板
            if matched_keyword and matched_templates:
                template = random.choice(matched_templates)
                tts_text = template.format(user_name=user_name, content=content)
                    
        # 如果有需要播报的TTS文本，则输出
        if tts_text:
            print(f"[TTS] {tts_text}")
            # 这里应该调用实际的TTS播放函数
            play_tts(tts_text)
        
    def update_status(self, status):
        """更新状态显示"""
        self.status_label.setText(f"状态: {status}")
        
    def update_display(self):
        """更新显示"""
        pass
        
    def clear_display(self):
        """清空显示区域"""
        self.danmaku_display.clear()
        
    def on_filter_changed(self):
        """筛选条件改变时的处理"""
        # 这里可以根据需要添加筛选逻辑
        pass
        
    def select_all_filters(self):
        """全选所有筛选项"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(True)
            
    def deselect_all_filters(self):
        """取消全选所有筛选项"""
        for checkbox in self.filter_checkboxes.values():
            checkbox.setChecked(False)
            
    def open_tts_config(self):
        """打开TTS配置对话框"""
        dialog = TTSConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tts_config()
            
    def load_tts_config(self):
        """加载TTS配置"""
        config_file = "tts_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.tts_config = json.load(f)
            except Exception as e:
                print(f"加载TTS配置失败: {e}")
                self.tts_config = {}
        else:
            self.tts_config = {}
        
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.worker:
            self.worker.stop_listening()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = DouyinLiveGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

def play_tts(text):
    """
    播放TTS文本
    
    Args:
        text (str): 要播放的文本
    """
    def _play():
        try:
            import asyncio
            from edgetts.play_audio_async import play_text
            asyncio.run(play_text(text))
        except Exception as e:
            print(f"TTS播放出错: {e}")
    
    # 在新线程中播放TTS，避免阻塞GUI
    tts_thread = threading.Thread(target=_play, daemon=True)
    tts_thread.start()
