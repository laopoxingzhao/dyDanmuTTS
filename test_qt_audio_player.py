#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Qt音频播放器测试脚本

用于测试基于Qt的音频播放器功能是否正常
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QSlider
from PyQt5.QtCore import Qt, QTimer

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tool.qt_audio_player import get_qt_audio_player
from config.log import g_logger


class QtAudioPlayerTest(QWidget):
    """Qt音频播放器测试界面"""
    
    def __init__(self):
        super().__init__()
        self.audio_player = get_qt_audio_player()
        self.test_file = None
        self.init_ui()
        self.find_test_audio()
        
    def init_ui(self):
        """初始化测试界面"""
        self.setWindowTitle("Qt音频播放器测试")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("状态: 未初始化")
        layout.addWidget(self.status_label)
        
        # 测试文件标签
        self.file_label = QLabel("测试文件: 未找到")
        layout.addWidget(self.file_label)
        
        # 初始化按钮
        self.init_btn = QPushButton("初始化音频播放器")
        self.init_btn.clicked.connect(self.initialize_player)
        layout.addWidget(self.init_btn)
        
        # 播放按钮
        self.play_btn = QPushButton("播放测试音频")
        self.play_btn.clicked.connect(self.play_test_audio)
        self.play_btn.setEnabled(False)
        layout.addWidget(self.play_btn)
        
        # 暂停按钮
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_audio)
        self.pause_btn.setEnabled(False)
        layout.addWidget(self.pause_btn)
        
        # 恢复按钮
        self.resume_btn = QPushButton("恢复")
        self.resume_btn.clicked.connect(self.resume_audio)
        self.resume_btn.setEnabled(False)
        layout.addWidget(self.resume_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        # 音量滑块
        self.volume_label = QLabel("音量: 100%")
        layout.addWidget(self.volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        layout.addWidget(self.volume_slider)
        
        # 统计信息按钮
        self.stats_btn = QPushButton("显示统计信息")
        self.stats_btn.clicked.connect(self.show_stats)
        layout.addWidget(self.stats_btn)
        
        # 清理缓存按钮
        self.clear_cache_btn = QPushButton("清空缓存")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        layout.addWidget(self.clear_cache_btn)
        
        self.setLayout(layout)
        
        # 定时器更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(500)  # 每500ms更新一次状态
        
    def find_test_audio(self):
        """查找测试音频文件"""
        # 尝试查找现有的音频文件
        possible_paths = [
            "output/test.mp3",
            "output/sample.mp3", 
            "test.mp3",
            "sample.mp3"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.test_file = path
                self.file_label.setText(f"测试文件: {path}")
                return
        
        # 如果没有找到，提示用户
        self.file_label.setText("测试文件: 未找到 (请将测试音频文件放在output/test.mp3)")
        
    def initialize_player(self):
        """初始化音频播放器"""
        try:
            success = self.audio_player.initialize()
            if success:
                self.status_label.setText("状态: 已初始化")
                self.init_btn.setEnabled(False)
                if self.test_file:
                    self.play_btn.setEnabled(True)
                g_logger.info("Qt音频播放器初始化成功")
            else:
                self.status_label.setText("状态: 初始化失败")
                g_logger.error("Qt音频播放器初始化失败")
        except Exception as e:
            self.status_label.setText(f"状态: 初始化错误 - {str(e)}")
            g_logger.error(f"初始化音频播放器时出错: {e}")
    
    def play_test_audio(self):
        """播放测试音频"""
        if not self.test_file:
            self.status_label.setText("状态: 没有测试音频文件")
            return
        
        try:
            # 预加载音频
            self.audio_player.preload_audio(self.test_file, "test")
            
            # 播放音频
            success = self.audio_player.play_file(self.test_file, "test")
            
            if success:
                self.status_label.setText("状态: 正在播放")
                self.play_btn.setEnabled(False)
                self.pause_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                g_logger.info(f"开始播放测试音频: {self.test_file}")
            else:
                self.status_label.setText("状态: 播放失败")
                g_logger.error("播放测试音频失败")
                
        except Exception as e:
            self.status_label.setText(f"状态: 播放错误 - {str(e)}")
            g_logger.error(f"播放测试音频时出错: {e}")
    
    def pause_audio(self):
        """暂停音频"""
        try:
            self.audio_player.pause()
            self.status_label.setText("状态: 已暂停")
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            g_logger.info("音频播放已暂停")
        except Exception as e:
            g_logger.error(f"暂停音频时出错: {e}")
    
    def resume_audio(self):
        """恢复音频"""
        try:
            self.audio_player.resume()
            self.status_label.setText("状态: 正在播放")
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            g_logger.info("音频播放已恢复")
        except Exception as e:
            g_logger.error(f"恢复音频时出错: {e}")
    
    def stop_audio(self):
        """停止音频"""
        try:
            self.audio_player.stop()
            self.status_label.setText("状态: 已停止")
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            g_logger.info("音频播放已停止")
        except Exception as e:
            g_logger.error(f"停止音频时出错: {e}")
    
    def on_volume_changed(self, value):
        """音量变化处理"""
        try:
            volume = value / 100.0
            self.audio_player.set_volume(volume)
            self.volume_label.setText(f"音量: {value}%")
        except Exception as e:
            g_logger.error(f"设置音量时出错: {e}")
    
    def show_stats(self):
        """显示统计信息"""
        try:
            stats = self.audio_player.get_stats()
            device_info = self.audio_player.get_device_info()
            
            stats_text = "=== 播放统计 ===\n"
            stats_text += f"总播放次数: {stats['total_played']}\n"
            stats_text += f"缓存命中率: {stats['cache_hit_rate']:.1%}\n"
            stats_text += f"预加载数量: {stats['preloaded_count']}\n"
            stats_text += f"平均加载时间: {stats['average_load_time']:.3f}s\n\n"
            
            stats_text += "=== 设备信息 ===\n"
            stats_text += f"已初始化: {device_info.get('initialized', False)}\n"
            stats_text += f"采样率: {device_info.get('sample_rate', 0)}\n"
            stats_text += f"缓冲区大小: {device_info.get('buffer_size', 0)}\n"
            stats_text += f"可用状态: {device_info.get('available', False)}\n"
            
            print(stats_text)
            g_logger.info("显示播放统计信息")
            
        except Exception as e:
            g_logger.error(f"获取统计信息时出错: {e}")
    
    def clear_cache(self):
        """清空缓存"""
        try:
            self.audio_player.clear_preloaded_cache()
            self.status_label.setText("状态: 缓存已清空")
            g_logger.info("音频缓存已清空")
        except Exception as e:
            g_logger.error(f"清空缓存时出错: {e}")
    
    def update_status(self):
        """更新状态显示"""
        try:
            if self.audio_player.initialized:
                if self.audio_player.is_playing():
                    if not self.status_label.text().startswith("状态: 正在播放"):
                        self.status_label.setText("状态: 正在播放")
                elif self.audio_player.is_paused():
                    if not self.status_label.text().startswith("状态: 已暂停"):
                        self.status_label.setText("状态: 已暂停")
                else:
                    if not self.status_label.text().startswith("状态: 已停止"):
                        self.status_label.setText("状态: 已停止")
        except Exception as e:
            g_logger.error(f"更新状态时出错: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            if self.audio_player:
                self.audio_player.shutdown()
                g_logger.info("Qt音频播放器测试程序已关闭")
        except Exception as e:
            g_logger.error(f"关闭音频播放器时出错: {e}")
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    test_window = QtAudioPlayerTest()
    test_window.show()
    
    g_logger.info("Qt音频播放器测试程序已启动")
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()