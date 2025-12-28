import queue
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re
import hashlib
from typing import Dict, Set, Optional, List, Tuple
from dataclasses import dataclass
from config.log import g_logger


@dataclass
class MessageStats:
    """消息统计信息"""
    count: int = 0
    last_time: float = 0
    users: Set[str] = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = set()


class SmartDeduplicator:
    """智能去重器"""
    
    def __init__(self, time_window: int = 30, similarity_threshold: float = 0.8):
        self.time_window = time_window
        self.similarity_threshold = similarity_threshold
        self.message_cache: Dict[str, float] = {}  # 消息哈希 -> 时间戳
        self.pattern_cache: Dict[str, float] = {}  # 模式哈希 -> 时间戳
        self.lock = threading.RLock()
        
        # 常见无意义消息模式
        self.ignore_patterns = [
            r'^[0-9]+$',  # 纯数字
            r'^[6-9]+$',   # 666, 777, 888, 999等
            r'^[.。！!？?]+$',  # 纯标点
            r'^(哈哈|呵呵|嘻嘻|嘿嘿)+$',  # 纯笑声
            r'^(好|不错|可以|棒|赞)+$',  # 纯赞美
            r'^(？|\?|！|\!)+$',  # 纯疑问或感叹
        ]
        
        # 编译正则表达式
        self.compiled_patterns = [re.compile(pattern) for pattern in self.ignore_patterns]
    
    def _get_message_hash(self, content: str) -> str:
        """获取消息内容哈希"""
        # 标准化内容：去除多余空格、转换为小写
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def _get_pattern_hash(self, content: str) -> str:
        """获取消息模式哈希（忽略具体数字等）"""
        # 将数字替换为占位符
        pattern = re.sub(r'\d+', '{NUM}', content.strip().lower())
        # 将连续相同字符替换为单个字符
        pattern = re.sub(r'(.)\1+', r'\1', pattern)
        return hashlib.md5(pattern.encode('utf-8')).hexdigest()
    
    def _is_meaningless_message(self, content: str) -> bool:
        """检查是否为无意义消息"""
        content = content.strip()
        
        # 检查长度
        if len(content) < 1:
            return True
        
        # 检查是否匹配忽略模式
        for pattern in self.compiled_patterns:
            if pattern.match(content):
                return True
        
        # 检查是否为单个字符重复
        if len(set(content)) == 1 and len(content) > 3:
            return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单的编辑距离算法）"""
        if not text1 or not text2:
            return 0.0
        
        # 标准化
        text1 = text1.strip().lower()
        text2 = text2.strip().lower()
        
        # 如果完全相同
        if text1 == text2:
            return 1.0
        
        # 简单的相似度计算：共同字符比例
        set1 = set(text1)
        set2 = set(text2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def should_filter_message(self, content: str, user_name: str = "", msg_type: str = "") -> Tuple[bool, str]:
        """
        判断是否应该过滤此消息
        
        Returns:
            Tuple[bool, str]: (是否过滤, 过滤原因)
        """
        current_time = time.time()
        
        with self.lock:
            # 检查是否为无意义消息
            if self._is_meaningless_message(content):
                return True, "无意义消息"
            
            # 获取消息哈希
            content_hash = self._get_message_hash(content)
            pattern_hash = self._get_pattern_hash(content)
            
            # 检查完全相同的消息
            if content_hash in self.message_cache:
                last_time = self.message_cache[content_hash]
                if current_time - last_time < self.time_window:
                    return True, f"重复消息（{current_time - last_time:.1f}秒内）"
            
            # 检查相似模式消息
            if pattern_hash in self.pattern_cache:
                last_time = self.pattern_cache[pattern_hash]
                if current_time - last_time < self.time_window / 2:  # 模式匹配的时间窗口更短
                    return True, f"相似模式消息（{current_time - last_time:.1f}秒内）"
            
            # 对于聊天消息，进行更严格的检查
            if msg_type == 'WebcastChatMessage':
                # 检查是否过于简单（短消息）
                if len(content.strip()) < 2:
                    return True, "消息过短"
                
                # 检查是否为纯表情或符号
                if not re.search(r'[a-zA-Z\u4e00-\u9fff]', content):
                    return True, "纯表情或符号"
            
            # 更新缓存
            self.message_cache[content_hash] = current_time
            self.pattern_cache[pattern_hash] = current_time
            
            # 清理过期缓存
            self._cleanup_expired_cache(current_time)
            
            return False, ""
    
    def _cleanup_expired_cache(self, current_time: float):
        """清理过期的缓存条目"""
        expired_keys = []
        
        # 清理消息缓存
        for key, timestamp in self.message_cache.items():
            if current_time - timestamp > self.time_window * 2:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.message_cache[key]
        
        # 清理模式缓存
        expired_keys = []
        for key, timestamp in self.pattern_cache.items():
            if current_time - timestamp > self.time_window:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.pattern_cache[key]
    
    def clear_cache(self):
        """清空所有缓存"""
        with self.lock:
            self.message_cache.clear()
            self.pattern_cache.clear()


class MessageAnalyzer:
    """消息分析器"""
    
    def __init__(self):
        self.stats: Dict[str, MessageStats] = {}
        self.lock = threading.RLock()
        
        # 重要关键词
        self.important_keywords = {
            '礼物': ['送出', '赠送', '礼物', '打赏'],
            '关注': ['关注', '粉丝', '加入粉丝团'],
            '互动': ['主播', '老师', '666', '厉害', '棒'],
            '问题': ['怎么', '为什么', '什么', '如何', '?', '？'],
        }
    
    def analyze_message(self, content: str, user_name: str, msg_type: str) -> Dict:
        """分析消息并返回分析结果"""
        result = {
            'importance_score': 1,  # 重要性评分 1-5
            'category': 'normal',    # 消息类别
            'is_question': False,    # 是否为问题
            'has_mention': False,    # 是否提及主播
            'keywords': [],          # 关键词列表
        }
        
        content_lower = content.lower()
        
        # 检查关键词
        for category, keywords in self.important_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    result['keywords'].append(keyword)
                    if category == '礼物':
                        result['importance_score'] = 5
                        result['category'] = 'gift'
                    elif category == '关注':
                        result['importance_score'] = 4
                        result['category'] = 'follow'
                    elif category == '互动':
                        result['importance_score'] = 3
                        result['category'] = 'interaction'
                    elif category == '问题':
                        result['is_question'] = True
                        result['importance_score'] = max(result['importance_score'], 3)
                        result['category'] = 'question'
        
        # 检查是否提及主播
        host_mentions = ['主播', '老师', 'UP主', '作者']
        if any(mention in content for mention in host_mentions):
            result['has_mention'] = True
            result['importance_score'] = min(result['importance_score'] + 1, 5)
        
        # 检查消息长度（长消息可能更重要）
        if len(content) > 20:
            result['importance_score'] = min(result['importance_score'] + 1, 5)
        
        # 更新统计
        with self.lock:
            key = f"{msg_type}:{result['category']}"
            if key not in self.stats:
                self.stats[key] = MessageStats()
            
            self.stats[key].count += 1
            self.stats[key].last_time = time.time()
            self.stats[key].users.add(user_name)
        
        return result
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            return {
                category: {
                    'count': stats.count,
                    'last_time': stats.last_time,
                    'unique_users': len(stats.users)
                }
                for category, stats in self.stats.items()
            }


class OptimizedTtsQueue:
    """
    优化的TTS队列系统
    集成智能去重、消息分析和优先级处理
    """
    
    def __init__(self, 
                 dedup_time_window: int = 30,
                 min_interval: int = 5,
                 max_queue_size: int = 20,
                 enable_smart_filter: bool = True):
        """
        初始化优化的TTS队列
        
        Args:
            dedup_time_window: 去重时间窗口（秒）
            min_interval: 同类型消息最小间隔（秒）
            max_queue_size: 队列最大长度
            enable_smart_filter: 是否启用智能过滤
        """
        self.queue = queue.PriorityQueue(maxsize=max_queue_size)
        self.deduplicator = SmartDeduplicator(time_window=dedup_time_window) if enable_smart_filter else None
        self.analyzer = MessageAnalyzer()
        
        # 类型控制
        self.type_last_time = defaultdict(float)
        self.type_counters = defaultdict(int)
        
        # 配置
        self.min_interval = min_interval
        self.max_queue_size = max_queue_size
        self.enable_smart_filter = enable_smart_filter
        
        # 锁
        self.lock = threading.RLock()
        
        # 统计
        self.stats = {
            'total_received': 0,
            'filtered_count': 0,
            'queued_count': 0,
            'filter_reasons': defaultdict(int)
        }
    
    def put(self, msg_type: str, content: str, user_name: str = None, 
            gift_name: str = None, gift_count: int = None, priority: int = None):
        """
        添加消息到TTS队列
        
        Args:
            msg_type: 消息类型
            content: 消息内容
            user_name: 用户名
            gift_name: 礼物名称
            gift_count: 礼物数量
            priority: 自定义优先级（可选）
        
        Returns:
            bool: 是否成功添加到队列
        """
        with self.lock:
            self.stats['total_received'] += 1
            
            # 生成TTS文本
            tts_text = self._generate_tts_text(msg_type, content, user_name, gift_name, gift_count)
            if not tts_text:
                self.stats['filtered_count'] += 1
                self.stats['filter_reasons']['empty_content'] += 1
                return False
            
            # 智能去重检查
            if self.enable_smart_filter and self.deduplicator:
                should_filter, reason = self.deduplicator.should_filter_message(
                    tts_text, user_name or "", msg_type
                )
                if should_filter:
                    self.stats['filtered_count'] += 1
                    self.stats['filter_reasons'][reason] += 1
                    g_logger.debug(f"消息被过滤: {tts_text[:30]}... - {reason}")
                    return False
            
            # 消息分析
            analysis = self.analyzer.analyze_message(tts_text, user_name or "", msg_type)
            
            # 计算优先级
            if priority is None:
                priority = self._calculate_priority(msg_type, analysis, user_name)
            
            # 检查类型间隔
            current_time = time.time()
            if current_time - self.type_last_time[msg_type] < self.min_interval:
                # 对于高优先级消息，可以忽略间隔限制
                if priority > 2:  # 优先级数字越大，优先级越低
                    self.stats['filtered_count'] += 1
                    self.stats['filter_reasons']['type_interval'] += 1
                    g_logger.debug(f"消息因类型间隔被过滤: {tts_text[:30]}...")
                    return False
            
            # 检查队列是否已满
            if self.queue.full():
                # 尝试移除低优先级项目
                if not self._make_room_for_priority(priority):
                    self.stats['filtered_count'] += 1
                    self.stats['filter_reasons']['queue_full'] += 1
                    g_logger.warning("TTS队列已满且无法为高优先级消息腾出空间")
                    return False
            
            # 创建队列项目
            item = {
                'priority': priority,
                'content': tts_text,
                'msg_type': msg_type,
                'user_name': user_name,
                'timestamp': current_time,
                'analysis': analysis
            }
            
            # 添加到队列
            try:
                self.queue.put_nowait((priority, current_time, item))
                self.type_last_time[msg_type] = current_time
                self.type_counters[msg_type] += 1
                self.stats['queued_count'] += 1
                
                g_logger.debug(f"添加TTS项目: {tts_text[:30]}... (优先级: {priority})")
                return True
                
            except queue.Full:
                self.stats['filtered_count'] += 1
                self.stats['filter_reasons']['queue_full'] += 1
                return False
    
    def _calculate_priority(self, msg_type: str, analysis: Dict, user_name: str = None) -> int:
        """计算消息优先级"""
        base_priority = 3  # 默认优先级
        
        # 根据消息类型调整
        type_priorities = {
            'WebcastGiftMessage': 1,      # 礼物消息最高优先级
            'WebcastSocialMessage': 2,    # 关注消息
            'WebcastMemberMessage': 3,    # 进入消息
            'WebcastChatMessage': 4,      # 聊天消息
            'WebcastLikeMessage': 5,      # 点赞消息
            'WebcastFansclubMessage': 2,  # 粉丝团消息
        }
        
        base_priority = type_priorities.get(msg_type, 4)
        
        # 根据分析结果调整
        importance = analysis.get('importance_score', 1)
        if importance >= 5:
            base_priority = min(base_priority - 2, 1)
        elif importance >= 4:
            base_priority = min(base_priority - 1, 1)
        elif importance <= 2:
            base_priority = max(base_priority + 1, 5)
        
        # 特殊用户优先级（如果需要）
        # if user_name and user_name in self.vip_users:
        #     base_priority = min(base_priority - 1, 1)
        
        return max(1, min(base_priority, 5))  # 确保优先级在1-5范围内
    
    def _make_room_for_priority(self, new_priority: int) -> bool:
        """为新优先级的消息腾出空间"""
        if self.queue.empty():
            return True
        
        # 收集队列中的所有项目
        temp_items = []
        while not self.queue.empty():
            try:
                temp_items.append(self.queue.get_nowait())
            except queue.Empty:
                break
        
        # 按优先级排序
        temp_items.sort(key=lambda x: (x[0], x[1]))  # 按优先级和时间排序
        
        # 如果新消息优先级比现有最低优先级高，则移除最低优先级的项目
        if temp_items and new_priority < temp_items[-1][0]:
            # 移除优先级最低的项目
            removed_item = temp_items.pop()
            g_logger.debug(f"移除低优先级项目: {removed_item[2]['content'][:30]}...")
            
            # 重新添加剩余项目
            for item in temp_items:
                self.queue.put_nowait(item)
            
            return True
        else:
            # 重新添加所有项目
            for item in temp_items:
                self.queue.put_nowait(item)
            
            return False
    
    def _generate_tts_text(self, msg_type: str, content: str, user_name: str = None, 
                          gift_name: str = None, gift_count: int = None) -> str:
        """生成TTS文本"""
        user_display = user_name or "用户"
        
        if msg_type == 'WebcastMemberMessage':
            return f"{user_display}进入了直播间"
        elif msg_type == 'WebcastSocialMessage':
            return f"{user_display}关注了主播"
        elif msg_type == 'WebcastGiftMessage' and gift_name:
            count_str = f"x{gift_count}" if gift_count and gift_count > 1 else ""
            return f"{user_display}送出了{gift_name}{count_str}"
        elif msg_type == 'WebcastChatMessage' and content:
            return f"{user_display}说：{content}"
        elif msg_type == 'WebcastLikeMessage':
            return f"{user_display}点赞了"
        elif msg_type == 'WebcastFansclubMessage':
            if content.strip():
                return f"粉丝团消息：{content}"
            else:
                return f"{user_display}加入了粉丝团"
        else:
            return content or ""
    
    def get(self) -> Optional[Dict]:
        """从队列获取一个TTS消息"""
        try:
            priority, timestamp, item = self.queue.get_nowait()
            return item
        except queue.Empty:
            return None
    
    def empty(self) -> bool:
        """检查队列是否为空"""
        return self.queue.empty()
    
    def size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()
    
    def clear(self):
        """清空队列"""
        with self.lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            
            self.type_last_time.clear()
            self.type_counters.clear()
            
            if self.deduplicator:
                self.deduplicator.clear_cache()
            
            g_logger.info("已清空TTS队列")
    
    def get_stats(self) -> Dict:
        """获取队列统计信息"""
        with self.lock:
            stats = self.stats.copy()
            stats['queue_size'] = self.size()
            stats['filter_rate'] = stats['filtered_count'] / max(stats['total_received'], 1)
            stats['success_rate'] = stats['queued_count'] / max(stats['total_received'], 1)
            stats['type_counters'] = dict(self.type_counters)
            stats['filter_reasons'] = dict(self.stats['filter_reasons'])
            
            # 添加分析器统计
            stats['message_analysis'] = self.analyzer.get_stats()
            
            return stats
    
    def update_config(self, dedup_time_window: int = None, min_interval: int = None, 
                     max_queue_size: int = None, enable_smart_filter: bool = None):
        """更新配置参数"""
        with self.lock:
            if dedup_time_window is not None:
                if self.deduplicator:
                    self.deduplicator.time_window = dedup_time_window
            
            if min_interval is not None:
                self.min_interval = min_interval
            
            if max_queue_size is not None:
                self.max_queue_size = max_queue_size
                # 重新创建队列以应用新的大小限制
                old_items = []
                while not self.queue.empty():
                    try:
                        old_items.append(self.queue.get_nowait())
                    except queue.Empty:
                        break
                
                self.queue = queue.PriorityQueue(maxsize=max_queue_size)
                
                # 重新添加项目（按优先级）
                old_items.sort(key=lambda x: (x[0], x[1]))
                for item in old_items[:max_queue_size]:
                    self.queue.put_nowait(item)
            
            if enable_smart_filter is not None:
                self.enable_smart_filter = enable_smart_filter
                if enable_smart_filter and not self.deduplicator:
                    self.deduplicator = SmartDeduplicator()
                elif not enable_smart_filter and self.deduplicator:
                    self.deduplicator.clear_cache()
                    self.deduplicator = None
            
            g_logger.info(f"TTS队列配置已更新")


# 创建全局优化TTS队列实例
optimized_ttsq = OptimizedTtsQueue()