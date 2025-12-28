from threading import Thread
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from config.config import config_manager
import queue
from config.log import g_logger
from dy_danmu.liveMan import DouyinLiveWebFetcher
from tool.optimized_queue import optimized_ttsq
from tts.optimized_tts_handler import init_optimized_tts_handler
from tool.memory_manager import get_memory_manager
import time
from typing import Dict, Optional

checkbox_labels = {
    'WebcastChatMessage': '聊天消息',
    'WebcastGiftMessage': '礼物消息',
    'WebcastLikeMessage': '点赞消息',
    'WebcastMemberMessage': '进入消息',
    'WebcastSocialMessage': '关注',
    'WebcastFansclubMessage': '粉丝团消息',
    'WebcastEmojiChatMessage': '聊天表情包消息',
    'WebcastRoomStatsMessage': '直播间统计信息',
    'WebcastRoomUserSeqMessage': '直播间统计',
    'WebcastRoomMessage': '直播间信息',
    'WebcastRoomRankMessage': '直播间排行榜信息',
    'WebcastRoomStreamAdaptationMessage': '直播间流配置',
}


class OptimizedDanmuController:
    """优化的弹幕控制器，集成了所有TTS优化功能"""
    
    room_id = None
    
    def __init__(self):
        super().__init__()
        # 使用全局配置管理器
        self.config_manager = config_manager

        self.dy_fetcher = None
        self.dy_fetcher_thread = None
        
        # 使用优化的TTS队列
        self.tts_queue = optimized_ttsq
        self.danmu_queue = queue.Queue()
        
        # 初始化优化的TTS处理器
        self.tts_handler = init_optimized_tts_handler(self.config_manager)
        
        # 初始化内存管理器
        self.memory_manager = get_memory_manager()
        
        # 性能监控
        self.performance_stats = {
            'start_time': time.time(),
            'total_messages': 0,
            'tts_messages': 0,
            'filtered_messages': 0,
            'last_update': time.time()
        }
        
        # 预加载常用短语
        self._init_preload_phrases()
    
    def _init_preload_phrases(self):
        """初始化预加载常用短语"""
        self.common_phrases = [
            "欢迎来到直播间",
            "感谢关注",
            "谢谢支持",
            "666",
            "真厉害",
            "主播好棒"
        ]
        
        # 如果TTS处理器支持预加载，则预加载这些短语
        if hasattr(self.tts_handler, 'preload_audio'):
            g_logger.info("开始预加载常用TTS短语...")
            for phrase in self.common_phrases:
                try:
                    self.tts_handler.preload_audio(phrase)
                except Exception as e:
                    g_logger.warning(f"预加载短语失败 '{phrase}': {e}")
    
    def start(self, room_id):
        """启动弹幕控制器"""
        self.cleanup()
        """启动弹幕控制器"""
        self.room_id = room_id
        g_logger.info(f"启动优化的弹幕控制器，房间ID：{room_id}")
        
        # 重置统计
        self.performance_stats = {
            'start_time': time.time(),
            'total_messages': 0,
            'tts_messages': 0,
            'filtered_messages': 0,
            'last_update': time.time()
        }
        
        # 启动抖音直播抓取器
        self.dy_fetcher = DouyinLiveWebFetcher(room_id)
        self.dy_fetcher.fn_ptr = self.add_danmu
        
        # 启动抓取线程
        self.dy_fetcher_thread = Thread(target=self.dy_fetcher.start)
        self.dy_fetcher_thread.start()
        
        # 启动优化的TTS处理器
        if self.tts_handler:
            self.tts_handler.start()
            g_logger.info("优化的TTS处理器已启动")
    
    def add_danmu(self, method, danmu):
        """添加弹幕，使用优化的过滤和分发机制"""
        try:
            # 更新统计
            self.performance_stats['total_messages'] += 1
            
            if self.is_message_type_enabled(method):
                # 获取配置信息
                danmu_settings = self.config_manager.danmu_settings
                tts_settings = self.config_manager.tts_settings
                
                # 添加到基础队列（保持原有功能）
                self.danmu_queue.put((method, danmu))
                g_logger.debug(f"添加到基础队列: {method}---{danmu}")
                
                # 根据TTS配置决定是否添加到TTS队列
                if tts_settings.tts_enabled and self._should_add_to_tts_queue(method, tts_settings):
                    success = self._add_to_optimized_tts_queue(method, danmu)
                    if success:
                        self.performance_stats['tts_messages'] += 1
                    else:
                        self.performance_stats['filtered_messages'] += 1
                else:
                    self.performance_stats['filtered_messages'] += 1
            else:
                self.performance_stats['filtered_messages'] += 1
                
        except Exception as e:
            g_logger.error(f"添加弹幕失败: {e}")
    
    def is_message_type_enabled(self, message_type):
        """检查消息类型是否在配置中启用"""
        config_key = self.get_config_key_for_message_type(message_type)
        if config_key:
            danmu_settings = self.config_manager.danmu_settings
            return getattr(danmu_settings, config_key, True)
        return False

    def get_config_key_for_message_type(self, message_type):
        """获取消息类型对应的配置键名"""
        type_mapping = {
            'WebcastChatMessage': 'WebcastChatMessage',
            'WebcastGiftMessage': 'WebcastGiftMessage',
            'WebcastLikeMessage': 'WebcastLikeMessage',
            'WebcastMemberMessage': 'WebcastMemberMessage',
            'WebcastSocialMessage': 'WebcastSocialMessage',
            'WebcastFansclubMessage': 'WebcastFansclubMessage',
            'WebcastEmojiChatMessage': 'WebcastEmojiChatMessage',
            'WebcastRoomStatsMessage': 'WebcastRoomStatsMessage',
            'WebcastRoomUserSeqMessage': 'WebcastRoomUserSeqMessage',
            'WebcastRoomMessage': 'WebcastRoomMessage',
            'WebcastRoomRankMessage': 'WebcastRoomRankMessage',
            'WebcastRoomStreamAdaptationMessage': 'WebcastRoomStreamAdaptationMessage'
        }
        return type_mapping.get(message_type)

    def cleanup(self):
        """清理资源"""
        g_logger.info("开始清理优化的弹幕控制器资源...")
        
        # 停止弹幕获取线程
        if self.dy_fetcher and hasattr(self.dy_fetcher, 'stop'):
            self.dy_fetcher.stop()
        
        # 停止优化的TTS处理器
        if self.tts_handler:
            self.tts_handler.stop()
            g_logger.info("优化的TTS处理器已停止")
        
        # 清空队列
        with self.danmu_queue.mutex:
            self.danmu_queue.queue.clear()
        
        # 清空TTS队列
        if self.tts_queue:
            self.tts_queue.clear()
        
        g_logger.info("优化的弹幕控制器资源清理完成")
    
    def get_danmu(self):
        """获取弹幕"""
        if self.danmu_queue.empty():
            return None, None
        else:
            return self.danmu_queue.get()

    def _should_add_to_tts_queue(self, method, tts_settings):
        """检查是否应该添加到TTS队列"""
        # 检查消息类型是否在TTS配置中启用
        tts_enabled_mapping = {
            'WebcastChatMessage': 'chat_tts',
            'WebcastGiftMessage': 'gift_tts',
            'WebcastLikeMessage': 'like_tts',
            'WebcastMemberMessage': 'member_tts',
            'WebcastSocialMessage': 'social_tts',
            'WebcastFansclubMessage': 'fansclub_tts'
        }
        
        tts_key = tts_enabled_mapping.get(method)
        if tts_key:
            return getattr(tts_settings, tts_key, True)
        return False

    def _add_to_optimized_tts_queue(self, method, danmu):
        """添加消息到优化的TTS队列"""
        try:
            # 提取消息参数
            user_name = danmu.get('user_name', '')
            content = danmu.get('content', '')
            gift_name = danmu.get('gift_name', '')
            gift_count = danmu.get('gift_count', danmu.get('count', 1))
            
            # 根据消息类型设置优先级
            priority = self._get_message_priority(method, danmu)
            
            # 添加到优化的TTS队列
            success = self.tts_queue.put(
                msg_type=method,
                content=content,
                user_name=user_name,
                gift_name=gift_name,
                gift_count=gift_count,
                priority=priority
            )
            
            if success:
                g_logger.debug(f"添加到优化TTS队列: {method} - {user_name}: {content[:30]}...")
            
            return success
            
        except Exception as e:
            g_logger.error(f"添加优化TTS消息失败: {e}")
            return False
    
    def _get_message_priority(self, method, danmu):
        """获取消息优先级"""
        # 礼物消息最高优先级
        if method == 'WebcastGiftMessage':
            gift_count = danmu.get('gift_count', danmu.get('count', 1))
            gift_name = danmu.get('gift_name', '')
            
            # 根据礼物价值调整优先级（这里可以根据实际礼物列表进行配置）
            high_value_gifts = ['火箭', '飞机', '游艇', '城堡']
            if any(gift in gift_name for gift in high_value_gifts):
                return 1  # 最高优先级
            elif gift_count >= 10:
                return 1
            else:
                return 2
        
        # 关注消息
        elif method == 'WebcastSocialMessage':
            return 2
        
        # 进入消息
        elif method == 'WebcastMemberMessage':
            return 3
        
        # 粉丝团消息
        elif method == 'WebcastFansclubMessage':
            return 2
        
        # 聊天消息 - 根据内容智能判断
        elif method == 'WebcastChatMessage':
            content = danmu.get('content', '').strip()
            user_name = danmu.get('user_name', '')
            
            # 提及主播的消息优先级高
            if any(keyword in content for keyword in ['主播', '老师', 'UP主']):
                return 2
            
            # 问题优先级较高
            if any(char in content for char in ['？', '?', '怎么', '什么', '为什么']):
                return 3
            
            # 长消息可能更重要
            if len(content) > 20:
                return 3
            
            # 普通消息
            return 4
        
        # 点赞消息优先级较低
        elif method == 'WebcastLikeMessage':
            return 5
        
        # 其他消息
        else:
            return 4
    
    def get_performance_stats(self) -> Dict:
        """获取性能统计信息"""
        current_time = time.time()
        runtime = current_time - self.performance_stats['start_time']
        
        stats = {
            'runtime_seconds': runtime,
            'total_messages': self.performance_stats['total_messages'],
            'tts_messages': self.performance_stats['tts_messages'],
            'filtered_messages': self.performance_stats['filtered_messages'],
            'messages_per_second': self.performance_stats['total_messages'] / max(runtime, 1),
            'tts_success_rate': self.performance_stats['tts_messages'] / max(self.performance_stats['total_messages'], 1),
        }
        
        # 添加队列统计
        if self.tts_queue:
            queue_stats = self.tts_queue.get_stats()
            stats.update({
                'queue_stats': queue_stats
            })
        
        # 添加TTS处理器统计
        if self.tts_handler and hasattr(self.tts_handler, 'get_stats'):
            tts_stats = self.tts_handler.get_stats()
            stats.update({
                'tts_handler_stats': tts_stats
            })
        
        return stats
    
    def get_queue_status(self) -> Dict:
        """获取队列状态信息"""
        status = {
            'danmu_queue_size': self.danmu_queue.qsize(),
        }
        
        if self.tts_queue:
            status['tts_queue_size'] = self.tts_queue.size()
            status['tts_queue_stats'] = self.tts_queue.get_stats()
        
        if self.tts_handler and hasattr(self.tts_handler, 'get_stats'):
            status['tts_handler_stats'] = self.tts_handler.get_stats()
        
        return status
    
    def update_tts_config(self, config_updates: Dict):
        """更新TTS配置"""
        try:
            for key, value in config_updates.items():
                if key == 'queue_settings':
                    # 更新队列配置
                    queue_settings = value
                    self.tts_queue.update_config(
                        dedup_time_window=queue_settings.get('dedup_time_window'),
                        min_interval=queue_settings.get('min_interval'),
                        max_queue_size=queue_settings.get('max_queue_size'),
                        enable_smart_filter=queue_settings.get('enable_smart_filter', True)
                    )
                elif key == 'tts_settings':
                    # 更新TTS处理器配置
                    for sub_key, sub_value in value.items():
                        self.config_manager.update_tts_setting(sub_key, sub_value)
                    
                    # 通知TTS处理器更新配置
                    if self.tts_handler:
                        self.tts_handler.update_config()
            
            g_logger.info(f"TTS配置已更新: {config_updates}")
            return True
            
        except Exception as e:
            g_logger.error(f"更新TTS配置失败: {e}")
            return False
    
    def clear_tts_cache(self):
        """清空TTS缓存"""
        try:
            if self.tts_handler and hasattr(self.tts_handler, 'clear_cache'):
                self.tts_handler.clear_cache()
            
            if self.tts_queue:
                self.tts_queue.clear()
            
            g_logger.info("TTS缓存已清空")
            return True
            
        except Exception as e:
            g_logger.error(f"清空TTS缓存失败: {e}")
            return False
    
    def pause_tts(self):
        """暂停TTS播放"""
        try:
            if self.tts_handler and hasattr(self.tts_handler, 'pause'):
                self.tts_handler.pause()
            else:
                # 如果没有暂停方法，通过禁用来实现
                self.config_manager.update_tts_setting('tts_enabled', False)
            
            g_logger.info("TTS播放已暂停")
            return True
            
        except Exception as e:
            g_logger.error(f"暂停TTS播放失败: {e}")
            return False
    
    def resume_tts(self):
        """恢复TTS播放"""
        try:
            if self.tts_handler and hasattr(self.tts_handler, 'resume'):
                self.tts_handler.resume()
            else:
                # 如果没有恢复方法，通过启用来实现
                self.config_manager.update_tts_setting('tts_enabled', True)
            
            g_logger.info("TTS播放已恢复")
            return True
            
        except Exception as e:
            g_logger.error(f"恢复TTS播放失败: {e}")
            return False
    
    def force_play_message(self, content: str, priority: int = 1):
        """强制播放消息（用于测试或特殊情况）"""
        try:
            if self.tts_handler and hasattr(self.tts_handler, 'add_tts_item'):
                return self.tts_handler.add_tts_item(content, priority)
            elif self.tts_queue:
                return self.tts_queue.put(
                    msg_type='ManualMessage',
                    content=content,
                    user_name='系统',
                    priority=priority
                )
            return False
            
        except Exception as e:
            g_logger.error(f"强制播放消息失败: {e}")
            return False
    
    def get_memory_stats(self) -> Dict:
        """获取内存使用统计"""
        memory_stats = {}
        
        if self.memory_manager:
            memory_stats = self.memory_manager.get_cleanup_stats()
        
        if self.tts_handler and hasattr(self.tts_handler, 'get_memory_stats'):
            tts_memory_stats = self.tts_handler.get_memory_stats()
            memory_stats.update(tts_memory_stats)
        
        return memory_stats
    
    def force_memory_cleanup(self):
        """强制内存清理"""
        if self.memory_manager:
            self.memory_manager.force_cleanup()
            g_logger.info("已执行强制内存清理")
            return True
        return False