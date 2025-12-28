from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QFrame, QGroupBox, QTextEdit,
                             QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
                             QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
import time
from datetime import datetime
from config.log import g_logger


class PerformanceMonitor(QWidget):
    """TTS性能监控面板"""
    
    # 定义信号
    clear_cache_signal = pyqtSignal()
    pause_tts_signal = pyqtSignal()
    resume_tts_signal = pyqtSignal()
    
    def __init__(self, danmu_controller=None):
        super().__init__()
        self.danmu_controller = danmu_controller
        self.init_ui()
        
        # 启动定时更新
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(1000)  # 每秒更新一次
        
        # 历史数据
        self.history_data = {
            'timestamps': [],
            'queue_sizes': [],
            'cache_hit_rates': [],
            'message_rates': []
        }
        self.max_history_points = 60  # 保留60秒的历史数据
    
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("TTS性能监控")
        self.setMinimumSize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 创建控制按钮区域
        self.create_control_panel(main_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 实时监控标签页
        realtime_widget = self.create_realtime_tab()
        self.tab_widget.addTab(realtime_widget, "实时监控")
        
        # 队列状态标签页
        queue_widget = self.create_queue_tab()
        self.tab_widget.addTab(queue_widget, "队列状态")
        
        # 缓存统计标签页
        cache_widget = self.create_cache_tab()
        self.tab_widget.addTab(cache_widget, "缓存统计")
        
        # 性能历史标签页
        history_widget = self.create_history_tab()
        self.tab_widget.addTab(history_widget, "性能历史")
        
        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
    
    def create_control_panel(self, parent_layout):
        """创建控制面板"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Box)
        control_layout = QHBoxLayout()
        
        # 控制按钮
        self.pause_btn = QPushButton("暂停TTS")
        self.pause_btn.clicked.connect(self.pause_tts)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        self.resume_btn = QPushButton("恢复TTS")
        self.resume_btn.clicked.connect(self.resume_tts)
        self.resume_btn.setEnabled(False)
        self.resume_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.clear_cache_btn = QPushButton("清空缓存")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.clear_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        self.force_test_btn = QPushButton("测试播放")
        self.force_test_btn.clicked.connect(self.test_tts)
        self.force_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        # 状态指示器
        self.status_label = QLabel("状态: 运行中")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px;")
        
        # 添加到布局
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.clear_cache_btn)
        control_layout.addWidget(self.force_test_btn)
        
        control_frame.setLayout(control_layout)
        parent_layout.addWidget(control_frame)
    
    def create_realtime_tab(self):
        """创建实时监控标签页"""
        widget = QWidget()
        layout = QGridLayout()
        
        # 实时统计卡片
        stats_group = QGroupBox("实时统计")
        stats_layout = QGridLayout()
        
        # 消息统计
        self.total_messages_label = self.create_stat_label("总消息数", "0")
        self.tts_messages_label = self.create_stat_label("TTS消息", "0")
        self.filtered_messages_label = self.create_stat_label("过滤消息", "0")
        self.message_rate_label = self.create_stat_label("消息速率", "0 msg/s")
        
        stats_layout.addWidget(self.total_messages_label, 0, 0)
        stats_layout.addWidget(self.tts_messages_label, 0, 1)
        stats_layout.addWidget(self.filtered_messages_label, 1, 0)
        stats_layout.addWidget(self.message_rate_label, 1, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group, 0, 0, 1, 2)
        
        # TTS处理器统计
        tts_group = QGroupBox("TTS处理器")
        tts_layout = QGridLayout()
        
        self.cache_hit_rate_label = self.create_stat_label("缓存命中率", "0%")
        self.avg_gen_time_label = self.create_stat_label("平均生成时间", "0ms")
        self.avg_play_time_label = self.create_stat_label("平均播放时间", "0ms")
        self.total_played_label = self.create_stat_label("总播放次数", "0")
        
        tts_layout.addWidget(self.cache_hit_rate_label, 0, 0)
        tts_layout.addWidget(self.avg_gen_time_label, 0, 1)
        tts_layout.addWidget(self.avg_play_time_label, 1, 0)
        tts_layout.addWidget(self.total_played_label, 1, 1)
        
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group, 1, 0, 1, 2)
        
        # 队列状态
        queue_group = QGroupBox("队列状态")
        queue_layout = QGridLayout()
        
        self.queue_size_label = self.create_stat_label("队列大小", "0")
        self.cache_size_label = self.create_stat_label("缓存大小", "0")
        self.filter_rate_label = self.create_stat_label("过滤率", "0%")
        self.success_rate_label = self.create_stat_label("成功率", "0%")
        
        queue_layout.addWidget(self.queue_size_label, 0, 0)
        queue_layout.addWidget(self.cache_size_label, 0, 1)
        queue_layout.addWidget(self.filter_rate_label, 1, 0)
        queue_layout.addWidget(self.success_rate_label, 1, 1)
        
        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group, 2, 0, 1, 2)
        
        # 进度条
        progress_group = QGroupBox("系统负载")
        progress_layout = QVBoxLayout()
        
        self.queue_progress = self.create_progress_bar("队列使用率")
        self.cache_progress = self.create_progress_bar("缓存使用率")
        
        progress_layout.addWidget(self.queue_progress)
        progress_layout.addWidget(self.cache_progress)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group, 3, 0, 1, 2)
        
        widget.setLayout(layout)
        return widget
    
    def create_queue_tab(self):
        """创建队列状态标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 队列详细统计表
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(["消息类型", "计数", "最后时间", "优先级"])
        self.queue_table.horizontalHeader().setStretchLastSection(True)
        self.queue_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.queue_table)
        
        # 过滤原因统计
        filter_group = QGroupBox("过滤原因统计")
        filter_layout = QVBoxLayout()
        
        self.filter_text = QTextEdit()
        self.filter_text.setReadOnly(True)
        self.filter_text.setMaximumHeight(150)
        
        filter_layout.addWidget(self.filter_text)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_cache_tab(self):
        """创建缓存统计标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 缓存统计信息
        cache_info_group = QGroupBox("缓存信息")
        cache_info_layout = QGridLayout()
        
        self.cache_files_label = self.create_stat_label("缓存文件数", "0")
        self.cache_size_label = self.create_stat_label("缓存大小", "0 MB")
        self.cache_hits_label = self.create_stat_label("缓存命中", "0")
        self.cache_misses_label = self.create_stat_label("缓存未命中", "0")
        
        cache_info_layout.addWidget(self.cache_files_label, 0, 0)
        cache_info_layout.addWidget(self.cache_size_label, 0, 1)
        cache_info_layout.addWidget(self.cache_hits_label, 1, 0)
        cache_info_layout.addWidget(self.cache_misses_label, 1, 1)
        
        cache_info_group.setLayout(cache_info_layout)
        layout.addWidget(cache_info_group)
        
        # 缓存操作日志
        log_group = QGroupBox("缓存操作日志")
        log_layout = QVBoxLayout()
        
        self.cache_log = QTextEdit()
        self.cache_log.setReadOnly(True)
        self.cache_log.setMaximumHeight(200)
        
        log_layout.addWidget(self.cache_log)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_history_tab(self):
        """创建性能历史标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 性能趋势图（这里用简单的文本显示，实际可以用图表库）
        history_group = QGroupBox("性能趋势")
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setFont(QFont("Consolas", 9))
        
        history_layout.addWidget(self.history_text)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_stat_label(self, title: str, value: str) -> QWidget:
        """创建统计标签"""
        container = QWidget()
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 14, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: #2196F3;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        container.setLayout(layout)
        
        # 存储value_label的引用以便更新
        setattr(container, 'value_label', value_label)
        
        return container
    
    def create_progress_bar(self, title: str) -> QWidget:
        """创建进度条"""
        container = QWidget()
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(progress_bar)
        container.setLayout(layout)
        
        # 存储progress_bar的引用以便更新
        setattr(container, 'progress_bar', progress_bar)
        
        return container
    
    def update_stats(self):
        """更新统计信息"""
        if not self.danmu_controller:
            return
        
        try:
            # 获取性能统计
            stats = self.danmu_controller.get_performance_stats()
            queue_status = self.danmu_controller.get_queue_status()
            
            # 更新实时统计
            self.total_messages_label.value_label.setText(str(stats.get('total_messages', 0)))
            self.tts_messages_label.value_label.setText(str(stats.get('tts_messages', 0)))
            self.filtered_messages_label.value_label.setText(str(stats.get('filtered_messages', 0)))
            self.message_rate_label.value_label.setText(f"{stats.get('messages_per_second', 0):.1f} msg/s")
            
            # 更新TTS处理器统计
            tts_stats = stats.get('tts_handler_stats', {})
            self.cache_hit_rate_label.value_label.setText(f"{tts_stats.get('cache_hit_rate', 0):.1%}")
            self.avg_gen_time_label.value_label.setText(f"{tts_stats.get('avg_generation_time', 0)*1000:.0f}ms")
            self.avg_play_time_label.value_label.setText(f"{tts_stats.get('avg_playback_time', 0)*1000:.0f}ms")
            self.total_played_label.value_label.setText(str(tts_stats.get('total_played', 0)))
            
            # 更新队列状态
            self.queue_size_label.value_label.setText(str(queue_status.get('tts_queue_size', 0)))
            self.cache_size_label.value_label.setText(str(tts_stats.get('cache_size', 0)))
            self.filter_rate_label.value_label.setText(f"{stats.get('filter_rate', 0):.1%}")
            self.success_rate_label.value_label.setText(f"{stats.get('tts_success_rate', 0):.1%}")
            
            # 更新进度条
            queue_size = queue_status.get('tts_queue_size', 0)
            max_queue_size = 30  # 默认最大队列大小
            queue_usage = min(100, (queue_size / max_queue_size) * 100)
            self.queue_progress.progress_bar.setValue(int(queue_usage))
            
            cache_size = tts_stats.get('cache_size', 0)
            max_cache_size = 50  # 默认最大缓存大小
            cache_usage = min(100, (cache_size / max_cache_size) * 100)
            self.cache_progress.progress_bar.setValue(int(cache_usage))
            
            # 更新队列详细统计
            self.update_queue_table(queue_status)
            
            # 更新缓存统计
            self.update_cache_stats(tts_stats)
            
            # 更新历史数据
            self.update_history(stats, queue_status)
            
        except Exception as e:
            g_logger.error(f"更新性能统计失败: {e}")
    
    def update_queue_table(self, queue_status):
        """更新队列详细统计表"""
        try:
            queue_stats = queue_status.get('tts_queue_stats', {})
            type_counters = queue_stats.get('type_counters', {})
            
            self.queue_table.setRowCount(len(type_counters))
            
            for row, (msg_type, count) in enumerate(type_counters.items()):
                self.queue_table.setItem(row, 0, QTableWidgetItem(msg_type))
                self.queue_table.setItem(row, 1, QTableWidgetItem(str(count)))
                self.queue_table.setItem(row, 2, QTableWidgetItem("--"))  # 最后时间
                self.queue_table.setItem(row, 3, QTableWidgetItem("--"))  # 优先级
            
        except Exception as e:
            g_logger.error(f"更新队列表格失败: {e}")
    
    def update_cache_stats(self, tts_stats):
        """更新缓存统计"""
        try:
            self.cache_files_label.value_label.setText(str(tts_stats.get('cache_size', 0)))
            self.cache_hits_label.value_label.setText(str(tts_stats.get('cache_hits', 0)))
            self.cache_misses_label.value_label.setText(str(tts_stats.get('cache_misses', 0)))
            
            # 估算缓存大小（假设每个文件平均50KB）
            cache_size_mb = (tts_stats.get('cache_size', 0) * 50) / 1024
            self.cache_size_label.setText(f"{cache_size_mb:.1f} MB")
            
        except Exception as e:
            g_logger.error(f"更新缓存统计失败: {e}")
    
    def update_history(self, stats, queue_status):
        """更新历史数据"""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 添加到历史数据
            self.history_data['timestamps'].append(current_time)
            self.history_data['queue_sizes'].append(queue_status.get('tts_queue_size', 0))
            self.history_data['cache_hit_rates'].append(stats.get('tts_handler_stats', {}).get('cache_hit_rate', 0))
            self.history_data['message_rates'].append(stats.get('messages_per_second', 0))
            
            # 限制历史数据长度
            if len(self.history_data['timestamps']) > self.max_history_points:
                for key in self.history_data:
                    self.history_data[key] = self.history_data[key][-self.max_history_points:]
            
            # 更新历史显示
            self.update_history_display()
            
        except Exception as e:
            g_logger.error(f"更新历史数据失败: {e}")
    
    def update_history_display(self):
        """更新历史数据显示"""
        try:
            if not self.history_data['timestamps']:
                return
            
            history_text = "时间\t\t队列大小\t缓存命中率\t消息速率\n"
            history_text += "-" * 50 + "\n"
            
            # 显示最近10条记录
            start_idx = max(0, len(self.history_data['timestamps']) - 10)
            
            for i in range(start_idx, len(self.history_data['timestamps'])):
                timestamp = self.history_data['timestamps'][i]
                queue_size = self.history_data['queue_sizes'][i]
                cache_hit_rate = self.history_data['cache_hit_rates'][i]
                message_rate = self.history_data['message_rates'][i]
                
                history_text += f"{timestamp}\t{queue_size}\t\t{cache_hit_rate:.1%}\t\t{message_rate:.1f} msg/s\n"
            
            self.history_text.setText(history_text)
            
        except Exception as e:
            g_logger.error(f"更新历史显示失败: {e}")
    
    def pause_tts(self):
        """暂停TTS"""
        if self.danmu_controller:
            self.danmu_controller.pause_tts()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.status_label.setText("状态: 已暂停")
            self.status_label.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 14px;")
    
    def resume_tts(self):
        """恢复TTS"""
        if self.danmu_controller:
            self.danmu_controller.resume_tts()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.status_label.setText("状态: 运行中")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14px;")
    
    def clear_cache(self):
        """清空缓存"""
        if self.danmu_controller:
            self.danmu_controller.clear_tts_cache()
            self.cache_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 缓存已清空")
    
    def test_tts(self):
        """测试TTS播放"""
        if self.danmu_controller:
            test_message = f"这是一条测试消息，时间：{datetime.now().strftime('%H:%M:%S')}"
            self.danmu_controller.force_play_message(test_message, priority=1)
            self.cache_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 发送测试消息: {test_message}")
    
    def set_danmu_controller(self, controller):
        """设置弹幕控制器"""
        self.danmu_controller = controller
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        event.accept()