"""
缓存管理模块 - 管理TTS音频缓存
"""
import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional
from config.log import g_logger


class CacheManager:
    """TTS缓存管理器"""
    
    def __init__(self, cache_dir: str = "output/cache", max_age: int = 86400, max_size_mb: int = 500):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            max_age: 最大缓存时间（秒），默认24小时
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = Path(cache_dir)
        self.max_age = max_age
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存索引文件
        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_index()
        
        # 统计信息
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_files': 0,
            'total_size': 0
        }
        
        # 初始化统计
        self._update_stats()
        
        g_logger.info(f"缓存管理器初始化 - 目录: {cache_dir}, 最大时间: {max_age}秒, 最大大小: {max_size_mb}MB")
    
    def get_cached_file(self, text: str, voice: str) -> Optional[str]:
        """
        获取缓存的音频文件
        
        Args:
            text: 文本内容
            voice: 语音类型
            
        Returns:
            str or None: 缓存文件路径或None
        """
        cache_key = self._generate_cache_key(text, voice)
        
        if cache_key in self.cache_index:
            entry = self.cache_index[cache_key]
            file_path = self.cache_dir / entry['filename']
            
            # 检查文件是否存在
            if not file_path.exists():
                del self.cache_index[cache_key]
                self._save_index()
                self.stats['cache_misses'] += 1
                g_logger.debug(f"缓存文件不存在: {cache_key}")
                return None
            
            # 检查文件是否过期
            current_time = time.time()
            if current_time - entry['timestamp'] > self.max_age:
                try:
                    file_path.unlink()
                except Exception as e:
                    g_logger.warning(f"删除过期缓存文件失败: {e}")
                del self.cache_index[cache_key]
                self._save_index()
                self.stats['cache_misses'] += 1
                g_logger.debug(f"缓存文件已过期: {cache_key}")
                return None
            
            # 更新访问时间
            entry['last_access'] = current_time
            self._save_index()
            
            self.stats['cache_hits'] += 1
            g_logger.debug(f"缓存命中: {text[:30]}... -> {file_path}")
            return str(file_path)
        
        self.stats['cache_misses'] += 1
        return None
    
    def save_to_cache(self, text: str, voice: str, file_path: str) -> bool:
        """
        保存文件到缓存
        
        Args:
            text: 文本内容
            voice: 语音类型
            file_path: 音频文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                g_logger.error(f"要缓存的文件不存在: {file_path}")
                return False
            
            # 生成缓存键
            cache_key = self._generate_cache_key(text, voice)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 检查缓存大小限制
            if self._get_total_size() + file_size > self.max_size_bytes:
                self._cleanup_oldest()
            
            # 生成缓存文件名
            cache_filename = f"tts_{cache_key[:16]}.mp3"
            cache_file_path = self.cache_dir / cache_filename
            
            # 如果文件不在缓存目录，复制过去
            if Path(file_path) != cache_file_path:
                import shutil
                shutil.copy2(file_path, cache_file_path)
                file_path = str(cache_file_path)
            
            # 更新索引
            current_time = time.time()
            self.cache_index[cache_key] = {
                'filename': cache_filename,
                'text': text[:100],  # 只保存前100个字符
                'voice': voice,
                'timestamp': current_time,
                'last_access': current_time,
                'size': file_size
            }
            
            self._save_index()
            self._update_stats()
            
            g_logger.debug(f"保存到缓存: {text[:30]}... -> {cache_filename}")
            return True
            
        except Exception as e:
            g_logger.error(f"保存到缓存失败: {e}")
            return False
    
    def clear_cache(self):
        """清空所有缓存"""
        try:
            # 删除所有缓存文件
            for file in self.cache_dir.glob("tts_*.mp3"):
                try:
                    file.unlink()
                except Exception as e:
                    g_logger.warning(f"删除缓存文件失败: {file}, {e}")
            
            # 清空索引
            self.cache_index.clear()
            self._save_index()
            
            # 重置统计
            self.stats = {
                'cache_hits': 0,
                'cache_misses': 0,
                'total_files': 0,
                'total_size': 0
            }
            
            g_logger.info("缓存已清空")
            
        except Exception as e:
            g_logger.error(f"清空缓存失败: {e}")
    
    def cleanup_expired(self):
        """清理过期的缓存文件"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for cache_key, entry in self.cache_index.items():
                if current_time - entry['timestamp'] > self.max_age:
                    expired_keys.append(cache_key)
            
            # 删除过期文件
            for cache_key in expired_keys:
                entry = self.cache_index[cache_key]
                file_path = self.cache_dir / entry['filename']
                
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    g_logger.warning(f"删除过期缓存文件失败: {file_path}, {e}")
                
                del self.cache_index[cache_key]
            
            if expired_keys:
                self._save_index()
                self._update_stats()
                g_logger.info(f"清理了 {len(expired_keys)} 个过期缓存文件")
            
        except Exception as e:
            g_logger.error(f"清理过期缓存失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        self._update_stats()
        return self.stats.copy()
    
    def _generate_cache_key(self, text: str, voice: str) -> str:
        """
        生成缓存键
        
        Args:
            text: 文本内容
            voice: 语音类型
            
        Returns:
            str: 缓存键（MD5哈希）
        """
        content = f"{text}:{voice}".encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    def _load_index(self) -> Dict:
        """加载缓存索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            g_logger.warning(f"加载缓存索引失败: {e}")
        return {}
    
    def _save_index(self):
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            g_logger.error(f"保存缓存索引失败: {e}")
    
    def _get_total_size(self) -> int:
        """获取缓存总大小"""
        total = 0
        for entry in self.cache_index.values():
            total += entry.get('size', 0)
        return total
    
    def _update_stats(self):
        """更新统计信息"""
        self.stats['total_files'] = len(self.cache_index)
        self.stats['total_size'] = self._get_total_size() / 1024 / 1024  # 转换为MB
    
    def _cleanup_oldest(self):
        """清理最旧的缓存文件"""
        try:
            # 按最后访问时间排序
            sorted_entries = sorted(
                self.cache_index.items(),
                key=lambda x: x[1]['last_access']
            )
            
            # 删除最旧的10%
            num_to_remove = max(1, len(sorted_entries) // 10)
            
            for i in range(num_to_remove):
                cache_key, entry = sorted_entries[i]
                file_path = self.cache_dir / entry['filename']
                
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    g_logger.warning(f"删除旧缓存文件失败: {file_path}, {e}")
                
                del self.cache_index[cache_key]
            
            self._save_index()
            g_logger.info(f"清理了 {num_to_remove} 个旧缓存文件")
            
        except Exception as e:
            g_logger.error(f"清理旧缓存失败: {e}")