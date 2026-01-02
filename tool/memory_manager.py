import os
import gc
import threading
import time
import psutil
import glob
from typing import List, Dict, Callable, Optional
from pathlib import Path
from config.log import g_logger


class MemoryManager:
    """内存和临时文件管理器"""
    
    def __init__(self, 
                 max_memory_mb: int = 500, 
                 cleanup_interval: int = 60,
                 temp_dirs: List[str] = None):
        """
        初始化内存管理器
        
        Args:
            max_memory_mb: 最大内存使用量（MB）
            cleanup_interval: 清理间隔（秒）
            temp_dirs: 临时目录列表
        """
        self.max_memory_mb = max_memory_mb
        self.cleanup_interval = cleanup_interval
        self.temp_dirs = temp_dirs or ["output/temp", "output/cache"]
        
        self.is_running = False
        self.cleanup_thread = None
        self._lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            'cleanup_count': 0,
            'files_deleted': 0,
            'memory_freed': 0,
            'last_cleanup': 0,
            'total_runtime': 0
        }
        
        # 清理回调函数
        self.cleanup_callbacks: List[Callable] = []
        
        # 文件类型清理策略
        self.cleanup_strategies = {
            'temp_general': {
                'pattern': 'output/temp_*',
                'max_age': 600,  # 10分钟
                'max_count': 100
            },
            'log_files': {
                'pattern': 'log/*.log',
                'max_age': 86400,  # 24小时
                'max_count': 10
            }
        }
    
    def start(self):
        """启动内存管理器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        g_logger.info(f"内存管理器已启动 - 最大内存: {self.max_memory_mb}MB, 清理间隔: {self.cleanup_interval}s")
    
    def stop(self):
        """停止内存管理器"""
        self.is_running = False
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        
        # 执行最后一次清理
        self._perform_cleanup()
        
        g_logger.info("内存管理器已停止")
    
    def add_cleanup_callback(self, callback: Callable):
        """添加清理回调函数"""
        with self._lock:
            if callback not in self.cleanup_callbacks:
                self.cleanup_callbacks.append(callback)
                g_logger.debug("已添加清理回调函数")
    
    def remove_cleanup_callback(self, callback: Callable):
        """移除清理回调函数"""
        with self._lock:
            if callback in self.cleanup_callbacks:
                self.cleanup_callbacks.remove(callback)
                g_logger.debug("已移除清理回调函数")
    
    def get_memory_usage(self) -> Dict:
        """获取当前内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # 转换为MB
            rss_mb = memory_info.rss / 1024 / 1024
            vms_mb = memory_info.vms / 1024 / 1024
            
            # 获取系统内存信息
            system_memory = psutil.virtual_memory()
            
            return {
                'process_rss_mb': rss_mb,
                'process_vms_mb': vms_mb,
                'system_total_mb': system_memory.total / 1024 / 1024,
                'system_available_mb': system_memory.available / 1024 / 1024,
                'system_percent': system_memory.percent,
                'max_limit_mb': self.max_memory_mb,
                'usage_percent': (rss_mb / self.max_memory_mb) * 100
            }
            
        except Exception as e:
            g_logger.error(f"获取内存使用情况失败: {e}")
            return {}
    
    def force_cleanup(self):
        """强制执行清理"""
        g_logger.info("执行强制清理...")
        self._perform_cleanup()
        self._force_garbage_collection()
    
    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                start_time = time.time()
                
                # 检查内存使用
                memory_usage = self.get_memory_usage()
                usage_percent = memory_usage.get('usage_percent', 0)
                
                # 如果内存使用超过阈值，执行清理
                if usage_percent > 80:  # 80%阈值
                    g_logger.warning(f"内存使用过高 ({usage_percent:.1f}%)，执行清理...")
                    self._perform_cleanup()
                    self._force_garbage_collection()
                elif time.time() - self.stats['last_cleanup'] > self.cleanup_interval:
                    # 定期清理
                    self._perform_cleanup()
                
                # 更新运行时间统计
                self.stats['total_runtime'] += time.time() - start_time
                
                # 等待下次清理
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                g_logger.error(f"清理循环出错: {e}")
                time.sleep(10)  # 出错时等待10秒再继续
    
    def _perform_cleanup(self):
        """执行清理操作"""
        with self._lock:
            start_time = time.time()
            files_deleted = 0
            memory_freed = 0
            
            try:
                # 清理临时文件
                for strategy_name, strategy in self.cleanup_strategies.items():
                    deleted, freed = self._cleanup_files_by_strategy(strategy)
                    files_deleted += deleted
                    memory_freed += freed
                    
                    g_logger.debug(f"清理策略 {strategy_name}: 删除 {deleted} 个文件, 释放 {freed}MB")
                
                # 调用清理回调
                for callback in self.cleanup_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        g_logger.error(f"清理回调执行失败: {e}")
                
                # 更新统计
                self.stats['cleanup_count'] += 1
                self.stats['files_deleted'] += files_deleted
                self.stats['memory_freed'] += memory_freed
                self.stats['last_cleanup'] = time.time()
                
                cleanup_time = time.time() - start_time
                g_logger.info(f"清理完成: 删除 {files_deleted} 个文件, 释放 {memory_freed:.1f}MB, 耗时 {cleanup_time:.2f}s")
                
            except Exception as e:
                g_logger.error(f"执行清理失败: {e}")
    
    def _cleanup_files_by_strategy(self, strategy: Dict) -> tuple:
        """根据策略清理文件"""
        pattern = strategy.get('pattern', '')
        max_age = strategy.get('max_age', 300)
        max_count = strategy.get('max_count', 100)
        
        files_deleted = 0
        memory_freed = 0
        
        try:
            # 查找匹配的文件
            file_paths = glob.glob(pattern)
            
            if not file_paths:
                return 0, 0
            
            current_time = time.time()
            files_to_delete = []
            
            # 按修改时间排序
            file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            for file_path in file_paths:
                try:
                    if not os.path.exists(file_path):
                        continue
                    
                    file_stat = os.stat(file_path)
                    file_age = current_time - file_stat.st_mtime
                    file_size = file_stat.st_size
                    
                    # 检查文件年龄
                    if file_age > max_age:
                        files_to_delete.append((file_path, file_size))
                        continue
                    
                    # 检查文件数量限制
                    remaining_files = len(file_paths) - len(files_to_delete)
                    if remaining_files > max_count:
                        files_to_delete.append((file_path, file_size))
                        continue
                
                except Exception as e:
                    g_logger.warning(f"检查文件失败 {file_path}: {e}")
            
            # 删除文件
            for file_path, file_size in files_to_delete:
                try:
                    os.remove(file_path)
                    files_deleted += 1
                    memory_freed += file_size / 1024 / 1024  # 转换为MB
                    
                except Exception as e:
                    g_logger.warning(f"删除文件失败 {file_path}: {e}")
            
        except Exception as e:
            g_logger.error(f"清理文件策略执行失败: {e}")
        
        return files_deleted, memory_freed
    
    def _force_garbage_collection(self):
        """强制垃圾回收"""
        try:
            # 收集垃圾
            collected = gc.collect()
            
            # 获取垃圾回收统计
            stats = gc.get_stats()
            
            g_logger.debug(f"垃圾回收: 回收 {collected} 个对象, 统计: {stats}")
            
        except Exception as e:
            g_logger.error(f"垃圾回收失败: {e}")
    
    def get_cleanup_stats(self) -> Dict:
        """获取清理统计信息"""
        with self._lock:
            stats = self.stats.copy()
            stats['current_memory_usage'] = self.get_memory_usage()
            stats['temp_dirs'] = self.temp_dirs
            return stats
    
    def set_cleanup_strategy(self, name: str, strategy: Dict):
        """设置清理策略"""
        with self._lock:
            self.cleanup_strategies[name] = strategy
            g_logger.info(f"已更新清理策略: {name}")
    
    def remove_cleanup_strategy(self, name: str):
        """移除清理策略"""
        with self._lock:
            if name in self.cleanup_strategies:
                del self.cleanup_strategies[name]
                g_logger.info(f"已移除清理策略: {name}")
    
    def get_temp_dir_sizes(self) -> Dict[str, float]:
        """获取临时目录大小"""
        sizes = {}
        
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    total_size = 0
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                total_size += os.path.getsize(file_path)
                            except:
                                pass
                    
                    sizes[temp_dir] = total_size / 1024 / 1024  # 转换为MB
                else:
                    sizes[temp_dir] = 0
                    
            except Exception as e:
                g_logger.error(f"获取目录大小失败 {temp_dir}: {e}")
                sizes[temp_dir] = 0
        
        return sizes
    
    def create_temp_file(self, prefix: str = "temp", suffix: str = ".tmp") -> str:
        """创建临时文件"""
        try:
            import tempfile
            import uuid
            
            # 确保临时目录存在
            temp_dir = "output/temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 生成唯一文件名
            unique_id = str(uuid.uuid4())[:8]
            file_name = f"{prefix}_{unique_id}{suffix}"
            file_path = os.path.join(temp_dir, file_name)
            
            # 创建文件
            with open(file_path, 'w') as f:
                pass  # 创建空文件
            
            g_logger.debug(f"创建临时文件: {file_path}")
            return file_path
            
        except Exception as e:
            g_logger.error(f"创建临时文件失败: {e}")
            return ""


class TempFileManager:
    """临时文件管理器"""
    
    def __init__(self):
        self.temp_files: set = set()
        self._lock = threading.RLock()
    
    def add_temp_file(self, file_path: str):
        """添加临时文件到管理列表"""
        with self._lock:
            self.temp_files.add(file_path)
    
    def remove_temp_file(self, file_path: str):
        """从管理列表移除临时文件"""
        with self._lock:
            self.temp_files.discard(file_path)
    
    def cleanup_temp_files(self):
        """清理所有管理的临时文件"""
        with self._lock:
            for file_path in list(self.temp_files):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        g_logger.debug(f"清理临时文件: {file_path}")
                except Exception as e:
                    g_logger.warning(f"清理临时文件失败 {file_path}: {e}")
                finally:
                    self.temp_files.discard(file_path)
    
    def get_temp_file_count(self) -> int:
        """获取临时文件数量"""
        with self._lock:
            return len(self.temp_files)
    
    def get_temp_files(self) -> List[str]:
        """获取临时文件列表"""
        with self._lock:
            return list(self.temp_files)


# 全局内存管理器实例
memory_manager = MemoryManager()
temp_file_manager = TempFileManager()

def get_memory_manager() -> MemoryManager:
    """获取全局内存管理器实例"""
    return memory_manager

def get_temp_file_manager() -> TempFileManager:
    """获取全局临时文件管理器实例"""
    return temp_file_manager