"""
TTS控制器 - 整合所有TTS功能的主控制器
"""
import threading
import time
import os
import random
from typing import Dict, Optional, Any
from datetime import datetime

from .tts_engine import TTSEngine
from .audio_player import AudioPlayer
from .keyword_matcher import KeywordMatcher, KeywordRule
from .message_queue import MessageQueue, TTSMessage, MessageType as MsgType
from .cache_manager import CacheManager
from config.log import g_logger


class TTSController:
    """TTS主控制器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化TTS控制器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.is_running = False
        self.worker_thread = None
        self._stop_event = threading.Event()
        
        # 初始化各模块
        self._init_modules()
        
        # 统计信息
        self.stats = {
            'total_messages': 0,
            'keyword_replies': 0,
            'generated_files': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': None
        }
        
        g_logger.info("TTS控制器初始化完成")
    
    def _init_modules(self):
        """初始化各个模块"""
        # TTS引擎
        voice = self.config.get('voice', '晓晓')
        rate = self.config.get('rate', '+0%')
        volume = self.config.get('volume', '+0%')
        self.tts_engine = TTSEngine(voice, rate, volume)
        
        # 音频播放器
        self.audio_player = AudioPlayer()
        self.audio_player.set_volume(self.config.get('playback_volume', 80))
        self.audio_player.set_min_play_interval(self.config.get('play_interval', 0.5))
        
        # 关键词匹配器
        self.keyword_matcher = KeywordMatcher()
        self._load_keyword_rules()
        
        # 消息队列
        max_queue_size = self.config.get('max_queue_size', 30)
        self.message_queue = MessageQueue(max_size=max_queue_size)
        
        # 缓存管理器（仅在启用时初始化）
        self.enable_cache = self.config.get('enable_cache', True)
        if self.enable_cache:
            cache_dir = self.config.get('cache_dir', 'output/cache')
            max_age = self.config.get('cache_max_age', 86400)
            max_size_mb = self.config.get('cache_max_size_mb', 500)
            self.cache_manager = CacheManager(cache_dir, max_age, max_size_mb)
        else:
            self.cache_manager = None
    
    def _load_keyword_rules(self):
        """加载关键词规则"""
        rules = self.config.get('keyword_rules', {})
        
        for keyword, rule_config in rules.items():
            try:
                rule = KeywordRule(
                    keyword=keyword,
                    match_type=rule_config.get('match_type', 'contain'),
                    replies=rule_config.get('replies', []),
                    priority=rule_config.get('priority', 1),
                    cooldown=rule_config.get('cooldown', 10),
                    reply_mode=rule_config.get('reply_mode', 'queue'),
                    reply_probability=rule_config.get('reply_probability', 1.0)
                )
                self.keyword_matcher.add_rule(keyword, rule)
            except Exception as e:
                g_logger.error(f"加载关键词规则失败: {keyword}, 错误: {e}")
    
    def start(self):
        """启动TTS控制器"""
        if self.is_running:
            g_logger.warning("TTS控制器已在运行中")
            return
        
        self.is_running = True
        self._stop_event.clear()
        self.stats['start_time'] = time.time()
        
        # 启动工作线程
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        g_logger.info("TTS控制器已启动")
    
    def stop(self):
        """停止TTS控制器"""
        if not self.is_running:
            return
        
        self.is_running = False
        self._stop_event.set()
        
        # 等待工作线程结束
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        
        # 停止音频播放
        self.audio_player.stop()
        
        g_logger.info("TTS控制器已停止")
    
    def add_danmu(self, danmu_data: Dict[str, Any], method: str = 'WebcastChatMessage'):
        """
        添加弹幕到TTS处理
        
        Args:
            danmu_data: 弹幕数据
            method: 消息类型
        """
        if not self.is_running:
            return
        
        try:
            self.stats['total_messages'] += 1
            
            # 根据不同的消息类型处理
            if method == 'WebcastChatMessage':
                self._handle_chat_message(danmu_data)
            elif method == 'WebcastMemberMessage':
                self._handle_member_enter(danmu_data)
            elif method == 'WebcastGiftMessage':
                self._handle_gift_message(danmu_data)
            elif method == 'WebcastSocialMessage':
                self._handle_social_message(danmu_data)
            elif method == 'WebcastLikeMessage':
                self._handle_like_message(danmu_data)
            else:
                g_logger.debug(f"未处理的消息类型: {method}")
            
        except Exception as e:
            g_logger.error(f"处理弹幕失败: {e}")
    
    def _handle_chat_message(self, danmu_data: Dict[str, Any]):
        """
        处理聊天消息
        
        Args:
            danmu_data: 弹幕数据
        """
        # 提取信息
        user_name = danmu_data.get('user_name', '未知用户')
        content = danmu_data.get('content', '')
        user_id = danmu_data.get('user_id', user_name)
        
        # 关键词匹配
        match_result = self.keyword_matcher.match(content, user_id)
        
        if match_result:
            # 有关键词匹配，生成回复
            keyword, rule = match_result
            
            # 获取回复文本
            variables = {
                'user_name': user_name,
                'content': content,
                'keyword': keyword,
                'time': datetime.now().strftime("%H:%M:%S")
            }
            reply_text = rule.get_reply(variables)
            
            # 根据回复模式处理
            if rule.reply_mode == 'immediate':
                # 立即回复（高优先级）
                priority = 10
            else:
                # 队列回复
                priority = rule.priority
            
            self.message_queue.add_message(
                text=reply_text,
                priority=priority,
                message_type=MsgType.KEYWORD_REPLY,
                variables=variables
            )
            
            self.stats['keyword_replies'] += 1
            g_logger.debug(f"关键词回复已添加到队列: {keyword} -> {reply_text[:30]}...")
    
    def _handle_member_enter(self, danmu_data: Dict[str, Any]):
        """
        处理进入直播间消息
        
        Args:
            danmu_data: 进入消息数据
        """
        # 检查是否启用进入播报
        event_config = self.config.get('event_announcement', {})
        member_config = event_config.get('member_enter', {})
        
        if not member_config.get('enabled', False):
            return
        
        # 检查冷却时间
        if not self._check_event_cooldown('member_enter', danmu_data.get('user_id')):
            return
        
        user_name = danmu_data.get('user_name', '未知用户')
        gender = danmu_data.get('gender', '未知')
        
        # 获取播报模板
        templates = member_config.get('templates', ['欢迎 {user_name} 进入直播间'])
        if not templates:
            templates = ['欢迎 {user_name} 进入直播间']
        template = random.choice(templates)
        
        # 替换变量
        variables = {
            'user_name': user_name,
            'gender': gender,
            'time': datetime.now().strftime("%H:%M:%S")
        }
        announcement = template.format(**variables)
        
        # 添加到队列
        priority = member_config.get('priority', 5)
        self.message_queue.add_message(
            text=announcement,
            priority=priority,
            message_type=MsgType.MEMBER_ENTER,
            variables=variables
        )
        
        g_logger.debug(f"进入播报已添加到队列: {user_name}")
    
    def _handle_gift_message(self, danmu_data: Dict[str, Any]):
        """
        处理送礼消息
        
        Args:
            danmu_data: 礼物数据
        """
        # 检查是否启用送礼播报
        event_config = self.config.get('event_announcement', {})
        gift_config = event_config.get('gift_send', {})
        
        if not gift_config.get('enabled', False):
            return
        
        user_name = danmu_data.get('user_name', '未知用户')
        gift_name = danmu_data.get('gift_name', '未知礼物')
        gift_count = danmu_data.get('gift_count', 1)
        
        # 检查是否超过最小礼物数量
        min_count = gift_config.get('min_gift_count', 1)
        if gift_count < min_count:
            return
        
        # 检查冷却时间（可选）
        if gift_config.get('enable_cooldown', False):
            if not self._check_event_cooldown('gift_send', danmu_data.get('user_id')):
                return
        
        # 获取播报模板
        templates = gift_config.get('templates', ['感谢 {user_name} 送出的 {gift_name} {gift_count} 个'])
        if not templates:
            templates = ['感谢 {user_name} 送出的 {gift_name} {gift_count} 个']
        template = random.choice(templates)
        
        # 替换变量
        variables = {
            'user_name': user_name,
            'gift_name': gift_name,
            'gift_count': str(gift_count),
            'time': datetime.now().strftime("%H:%M:%S")
        }
        announcement = template.format(**variables)
        
        # 添加到队列
        priority = gift_config.get('priority', 7)
        self.message_queue.add_message(
            text=announcement,
            priority=priority,
            message_type=MsgType.GIFT_SEND,
            variables=variables
        )
        
        g_logger.debug(f"送礼播报已添加到队列: {user_name} - {gift_name}x{gift_count}")
    
    def _handle_social_message(self, danmu_data: Dict[str, Any]):
        """
        处理关注消息
        
        Args:
            danmu_data: 关注数据
        """
        # 检查是否启用关注播报
        event_config = self.config.get('event_announcement', {})
        follow_config = event_config.get('social_follow', {})
        
        if not follow_config.get('enabled', False):
            return
        
        # 检查冷却时间
        if not self._check_event_cooldown('social_follow', danmu_data.get('user_id')):
            return
        
        user_name = danmu_data.get('user_name', '未知用户')
        
        # 获取播报模板
        templates = follow_config.get('templates', ['感谢 {user_name} 的关注'])
        if not templates:
            templates = ['感谢 {user_name} 的关注']
        template = random.choice(templates)
        
        # 替换变量
        variables = {
            'user_name': user_name,
            'time': datetime.now().strftime("%H:%M:%S")
        }
        announcement = template.format(**variables)
        
        # 添加到队列
        priority = follow_config.get('priority', 6)
        self.message_queue.add_message(
            text=announcement,
            priority=priority,
            message_type=MsgType.SOCIAL_FOLLOW,
            variables=variables
        )
        
        g_logger.debug(f"关注播报已添加到队列: {user_name}")
    
    def _handle_like_message(self, danmu_data: Dict[str, Any]):
        """
        处理点赞消息
        
        Args:
            danmu_data: 点赞数据
        """
        # 检查是否启用点赞播报
        event_config = self.config.get('event_announcement', {})
        like_config = event_config.get('like', {})
        
        if not like_config.get('enabled', False):
            return
        
        user_name = danmu_data.get('user_name', '未知用户')
        count = danmu_data.get('count', 1)
        
        # 检查是否超过最小点赞数量
        min_count = like_config.get('min_like_count', 10)
        if count < min_count:
            return
        
        # 检查冷却时间（可选）
        if like_config.get('enable_cooldown', False):
            if not self._check_event_cooldown('like', danmu_data.get('user_id')):
                return
        
        # 获取播报模板
        templates = like_config.get('templates', ['{user_name} 点了 {count} 个赞'])
        if not templates:
            templates = ['{user_name} 点了 {count} 个赞']
        template = random.choice(templates)
        
        # 替换变量
        variables = {
            'user_name': user_name,
            'count': str(count),
            'time': datetime.now().strftime("%H:%M:%S")
        }
        announcement = template.format(**variables)
        
        # 添加到队列
        priority = like_config.get('priority', 4)
        self.message_queue.add_message(
            text=announcement,
            priority=priority,
            message_type=MsgType.LIKE,
            variables=variables
        )
        
        g_logger.debug(f"点赞播报已添加到队列: {user_name} - {count}个赞")
    
    def _check_event_cooldown(self, event_type: str, user_id: str = None) -> bool:
        """
        检查事件冷却时间
        
        Args:
            event_type: 事件类型
            user_id: 用户ID
            
        Returns:
            bool: 是否可以触发
        """
        # 初始化冷却字典
        if not hasattr(self, 'event_cooldowns'):
            self.event_cooldowns = {}
        
        current_time = time.time()
        event_config = self.config.get('event_announcement', {})
        specific_config = event_config.get(event_type, {})
        cooldown_seconds = specific_config.get('cooldown', 30)
        
        g_logger.debug(f"[冷却检查] 事件类型: {event_type}, 用户ID: {user_id}, 冷却时间: {cooldown_seconds}秒")
        
        # 生成冷却键
        # 对于送礼和点赞，使用 enable_cooldown 配置；对于进入和关注，使用 user_cooldown 配置
        if event_type in ['gift_send', 'like']:
            # 送礼和点赞使用 enable_cooldown
            enable_cooldown = specific_config.get('enable_cooldown', False)
            g_logger.debug(f"[冷却检查] {event_type} enable_cooldown: {enable_cooldown}")
            
            if enable_cooldown:
                cooldown_key = f"{event_type}_{user_id}" if user_id else event_type
            else:
                # 不启用冷却，直接返回True
                g_logger.debug(f"[冷却检查] {event_type} 冷却未启用，允许触发")
                return True
        else:
            # 进入和关注使用 user_cooldown
            user_cooldown = specific_config.get('user_cooldown', True)
            g_logger.debug(f"[冷却检查] {event_type} user_cooldown: {user_cooldown}")
            
            if user_id and user_cooldown:
                cooldown_key = f"{event_type}_{user_id}"
            else:
                cooldown_key = event_type
        
        # 检查冷却时间
        if cooldown_key in self.event_cooldowns:
            last_time = self.event_cooldowns[cooldown_key]
            elapsed = current_time - last_time
            g_logger.debug(f"[冷却检查] 冷却键: {cooldown_key}, 上次触发: {last_time:.2f}, 已过: {elapsed:.2f}秒")
            
            if elapsed < cooldown_seconds:
                g_logger.debug(f"[冷却检查] 冷却中，剩余 {cooldown_seconds - elapsed:.2f}秒，拒绝触发")
                return False
        
        # 更新冷却时间
        self.event_cooldowns[cooldown_key] = current_time
        g_logger.debug(f"[冷却检查] 更新冷却时间: {cooldown_key} -> {current_time:.2f}")
        return True
    
    def add_custom_message(self, text: str, priority: int = 5):
        """
        添加自定义消息
        
        Args:
            text: 消息文本
            priority: 优先级
        """
        if not self.is_running:
            return
        
        self.message_queue.add_message(
            text=text,
            priority=priority,
            message_type=MsgType.SYSTEM_MESSAGE
        )
    
    def _worker_loop(self):
        """工作线程循环"""
        while not self._stop_event.is_set():
            try:
                # 从队列获取消息
                message = self.message_queue.get_message(timeout=1.0)
                
                if message:
                    self._process_message(message)
                    
            except Exception as e:
                g_logger.error(f"工作线程错误: {e}")
                time.sleep(1)
    
    def _process_message(self, message: TTSMessage):
        """
        处理TTS消息
        
        Args:
            message: TTS消息对象
        """
        try:
            text = message.text
            voice = self.tts_engine.voice_name
            
            # 检查缓存（如果启用）
            cached_file = None
            if self.enable_cache and self.cache_manager:
                cached_file = self.cache_manager.get_cached_file(text, voice)
            
            if cached_file:
                # 缓存命中
                self.stats['cache_hits'] += 1
                g_logger.debug(f"使用缓存文件: {cached_file}")
            else:
                # 缓存未命中，生成TTS
                self.stats['cache_misses'] += 1
                
                # 生成临时文件名
                temp_dir = "output/temp"
                os.makedirs(temp_dir, exist_ok=True)
                timestamp = int(time.time() * 1000)
                temp_file = os.path.join(temp_dir, f"tts_{timestamp}.mp3")
                
                # 生成TTS
                if self.tts_engine.text_to_speech(text, temp_file):
                    # 保存到缓存（如果启用）
                    if self.enable_cache and self.cache_manager:
                        self.cache_manager.save_to_cache(text, voice, temp_file)
                    cached_file = temp_file
                    self.stats['generated_files'] += 1
                else:
                    g_logger.error(f"TTS生成失败: {text[:30]}...")
                    return
            
            # 播放音频
            self.audio_player.play(cached_file, wait=True)
            
        except Exception as e:
            g_logger.error(f"处理TTS消息失败: {e}")
    
    def update_config(self, config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            config: 新配置字典
        """
        self.config.update(config)
        
        # 更新TTS引擎配置
        if 'voice' in config:
            self.tts_engine.set_voice(config['voice'])
        if 'rate' in config:
            self.tts_engine.set_rate(config['rate'])
        if 'volume' in config:
            self.tts_engine.set_volume(config['volume'])
        
        # 更新播放器配置
        if 'playback_volume' in config:
            self.audio_player.set_volume(config['playback_volume'])
        if 'play_interval' in config:
            self.audio_player.set_min_play_interval(config['play_interval'])
        
        # 更新队列配置
        if 'max_queue_size' in config:
            self.message_queue.max_size = config['max_queue_size']
        
        g_logger.info("TTS配置已更新")
    
    def add_keyword_rule(self, keyword: str, rule: KeywordRule):
        """
        添加关键词规则
        
        Args:
            keyword: 关键词
            rule: 规则对象
        """
        self.keyword_matcher.add_rule(keyword, rule)
        
        # 保存到配置
        if 'keyword_rules' not in self.config:
            self.config['keyword_rules'] = {}
        
        self.config['keyword_rules'][keyword] = {
            'match_type': rule.match_type,
            'replies': rule.replies,
            'priority': rule.priority,
            'cooldown': rule.cooldown,
            'reply_mode': rule.reply_mode,
            'reply_probability': rule.reply_probability
        }
    
    def remove_keyword_rule(self, keyword: str):
        """
        移除关键词规则
        
        Args:
            keyword: 关键词
        """
        self.keyword_matcher.remove_rule(keyword)
        
        if 'keyword_rules' in self.config and keyword in self.config['keyword_rules']:
            del self.config['keyword_rules'][keyword]
    
    def clear_queue(self):
        """清空消息队列"""
        self.message_queue.clear()
        g_logger.info("TTS消息队列已清空")
    
    def clear_cache(self):
        """清空缓存"""
        if self.enable_cache and self.cache_manager:
            self.cache_manager.clear_cache()
            g_logger.info("TTS缓存已清空")
        else:
            g_logger.info("缓存未启用，无需清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        runtime = 0
        if self.stats['start_time']:
            runtime = time.time() - self.stats['start_time']
        
        # 合并各模块的统计信息
        stats = {
            'runtime_seconds': runtime,
            'total_messages': self.stats['total_messages'],
            'keyword_replies': self.stats['keyword_replies'],
            'generated_files': self.stats['generated_files'],
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'cache_hit_rate': self._calculate_hit_rate(),
            'queue_stats': self.message_queue.get_stats(),
            'keyword_stats': self.keyword_matcher.get_stats(),
            'cache_enabled': self.enable_cache
        }
        
        # 添加缓存统计（如果启用）
        if self.enable_cache and self.cache_manager:
            stats['cache_stats'] = self.cache_manager.get_stats()
        else:
            stats['cache_stats'] = {
                'cache_hits': 0,
                'cache_misses': 0,
                'total_files': 0,
                'total_size': 0
            }
        
        return stats
    
    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率"""
        total = self.stats['cache_hits'] + self.stats['cache_misses']
        if total == 0:
            return 0.0
        return self.stats['cache_hits'] / total