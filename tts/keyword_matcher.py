"""
关键词匹配引擎 - 匹配弹幕内容并生成回复
"""
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from config.log import g_logger


@dataclass
class KeywordRule:
    """关键词规则"""
    keyword: str
    match_type: str = 'contain'  # exact, contain, regex
    replies: List[str] = field(default_factory=list)
    priority: int = 1
    cooldown: int = 10  # 冷却时间（秒）
    reply_mode: str = 'queue'  # immediate, queue
    reply_probability: float = 1.0  # 回复概率 0-1
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.replies:
            self.replies = [f"你说了{self.keyword}"]
    
    def match(self, text: str) -> bool:
        """
        匹配文本
        
        Args:
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        try:
            if self.match_type == 'exact':
                return text.strip() == self.keyword
            elif self.match_type == 'contain':
                return self.keyword in text
            elif self.match_type == 'regex':
                return bool(re.search(self.keyword, text))
            else:
                return False
        except Exception as e:
            g_logger.error(f"关键词匹配失败: {self.keyword}, 错误: {e}")
            return False
    
    def get_reply(self, variables: Dict[str, str] = None) -> str:
        """
        获取回复文本
        
        Args:
            variables: 变量字典
            
        Returns:
            str: 回复文本
        """
        import random
        
        # 随机选择一条回复
        reply = random.choice(self.replies)
        
        # 替换变量
        if variables:
            for key, value in variables.items():
                reply = reply.replace(f"{{{key}}}", value)
        
        return reply


class KeywordMatcher:
    """关键词匹配器"""
    
    def __init__(self):
        self.rules: Dict[str, KeywordRule] = {}
        self.user_cooldowns: Dict[str, float] = {}  # 用户冷却时间
        self.keyword_cooldowns: Dict[str, float] = {}  # 关键词冷却时间
        
        # 统计信息
        self.stats = {
            'total_matches': 0,
            'total_replies': 0,
            'keyword_stats': {}  # 每个关键词的触发次数
        }
    
    def add_rule(self, keyword: str, rule: KeywordRule):
        """
        添加关键词规则
        
        Args:
            keyword: 关键词
            rule: 规则对象
        """
        self.rules[keyword] = rule
        self.stats['keyword_stats'][keyword] = 0
        g_logger.info(f"添加关键词规则: {keyword} (匹配方式: {rule.match_type})")
    
    def remove_rule(self, keyword: str):
        """
        移除关键词规则
        
        Args:
            keyword: 关键词
        """
        if keyword in self.rules:
            del self.rules[keyword]
            if keyword in self.stats['keyword_stats']:
                del self.stats['keyword_stats'][keyword]
            g_logger.info(f"移除关键词规则: {keyword}")
    
    def update_rule(self, keyword: str, rule: KeywordRule):
        """
        更新关键词规则
        
        Args:
            keyword: 关键词
            rule: 规则对象
        """
        self.rules[keyword] = rule
        g_logger.info(f"更新关键词规则: {keyword}")
    
    def match(self, text: str, user_id: str = None) -> Optional[Tuple[str, KeywordRule]]:
        """
        匹配文本并返回匹配的关键词和规则
        
        Args:
            text: 要匹配的文本
            user_id: 用户ID（用于冷却）
            
        Returns:
            Tuple[str, KeywordRule] or None: (关键词, 规则) 或 None
        """
        current_time = time.time()
        
        # 按优先级排序规则
        sorted_rules = sorted(
            self.rules.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        # 遍历所有规则
        for keyword, rule in sorted_rules:
            # 检查冷却时间
            if not self._check_cooldown(keyword, user_id, current_time, rule):
                continue
            
            # 检查是否匹配
            if rule.match(text):
                # 检查回复概率
                import random
                if random.random() > rule.reply_probability:
                    g_logger.debug(f"回复概率未触发: {keyword}")
                    continue
                
                # 更新统计
                self.stats['total_matches'] += 1
                self.stats['keyword_stats'][keyword] = \
                    self.stats['keyword_stats'].get(keyword, 0) + 1
                
                # 更新冷却时间
                if user_id:
                    self.user_cooldowns[user_id] = current_time
                self.keyword_cooldowns[keyword] = current_time
                
                g_logger.debug(f"关键词匹配成功: {keyword} -> {text[:30]}...")
                return keyword, rule
        
        return None
    
    def _check_cooldown(self, keyword: str, user_id: str, 
                       current_time: float, rule: KeywordRule) -> bool:
        """
        检查冷却时间
        
        Args:
            keyword: 关键词
            user_id: 用户ID
            current_time: 当前时间
            rule: 规则对象
            
        Returns:
            bool: 是否可以触发
        """
        # 检查用户冷却
        if user_id and user_id in self.user_cooldowns:
            if current_time - self.user_cooldowns[user_id] < rule.cooldown:
                return False
        
        # 检查关键词冷却
        if keyword in self.keyword_cooldowns:
            if current_time - self.keyword_cooldowns[keyword] < rule.cooldown:
                return False
        
        return True
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_matches': 0,
            'total_replies': 0,
            'keyword_stats': {}
        }
        g_logger.info("关键词匹配统计已重置")
    
    def clear_cooldowns(self):
        """清空所有冷却时间"""
        self.user_cooldowns.clear()
        self.keyword_cooldowns.clear()
        g_logger.info("所有冷却时间已清空")