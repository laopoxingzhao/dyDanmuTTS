# DouyinLiveWebFetcher 日志系统

## 简介

本日志系统是为 DouyinLiveWebFetcher 项目专门设计的日志管理模块，提供了统一的日志记录和管理功能。

## 功能特点

- 同时输出日志到文件和控制台
- 按日期分割日志文件
- 支持多种日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- 统一的日志格式
- 线程安全
- 易于集成和使用

## 使用方法

### 1. 基本使用

在任何需要记录日志的 Python 文件中：

```python
from dy_danmu.log_manager import get_logger

logger = get_logger()
logger.info("这是一条信息日志")
logger.debug("这是一条调试日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")
logger.critical("这是一条严重错误日志")
```

### 2. 高级配置

如果需要自定义日志配置：

```python
from dy_danmu.log_manager import setup_logger

# 设置日志目录和级别
logger = setup_logger(log_dir="my_logs", log_level=logging.DEBUG)
logger.info("日志系统配置完成")
```

### 3. 在类中使用

```python
from dy_danmu.log_manager import get_logger

class MyClass:
    def __init__(self):
        self.logger = get_logger()
        self.logger.info("MyClass 实例已创建")
    
    def my_method(self):
        self.logger.debug("my_method 被调用")
```

## 日志格式

日志采用统一格式：

```
[时间] - [模块名] - [日志级别] - [消息内容]
```

示例：
```
2025-12-22 10:30:45,123 - DouyinLiveWebFetcher - INFO - 开始连接直播间
```

## 日志文件

- 日志文件存储在 `logs` 目录下（默认）
- 文件名格式：`douyin_live_YYYYMMDD.log`
- 每天自动创建新的日志文件

## 注意事项

1. 首次调用 `get_logger()` 时会自动初始化日志系统
2. 重复调用 `setup_logger()` 会重新配置日志系统
3. 日志目录会在首次写入日志时自动创建