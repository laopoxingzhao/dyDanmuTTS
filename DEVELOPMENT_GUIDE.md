# 开发指南

## 项目概述

本项目是一个用于抓取抖音直播弹幕的工具，支持命令行和图形界面两种使用方式，并集成了TTS语音播报功能。

## 项目结构

详见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 开发环境搭建

### 必需环境

1. Python 3.7+
2. Node.js v18.2.0 (或其他较新版本)
3. protoc 编译器 (版本 25.1)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 项目依赖说明

- `requests`: HTTP请求库
- `websocket-client`: WebSocket客户端
- `betterproto`: Protobuf编解码库
- `PyExecJS`: 在Python中执行JavaScript
- `mini-racer`: 另一种JavaScript执行引擎
- `edge-tts`: 微软Edge TTS服务接口
- `pygame`: 音频播放
- `opencv-python`: 视频播放相关功能
- `PyQt5`: GUI界面库

## 核心模块说明

### liveMan.py - 核心抓取模块

这是项目的核心模块，负责：
1. 通过JS计算请求参数签名
2. 发起HTTP请求获取直播信息
3. 建立WebSocket连接接收弹幕数据
4. 解析Protobuf格式的消息
5. 分发不同类型的消息

### message_handler.py - 消息处理模块

实现了消息队列机制：
- 提供线程安全的消息存取接口
- 控制消息队列的最大容量
- 防止内存溢出

### GUI模块

#### douyin_gui.py

完整功能的GUI程序，包括：
- 直播间连接管理
- 弹幕消息显示和过滤
- TTS语音播报配置和播放
- 实时统计数据展示

#### main_gui.py

项目主入口GUI，提供功能选择界面。

### TTS模块

#### edgetts/play_audio_async.py

基于Edge TTS的异步音频播放实现，使用pygame播放音频。

#### live_tts_main.py

TTS功能的命令行入口。

## 开发注意事项

### 1. 签名计算

抖音为了防止爬虫，对接口进行了签名保护，包括：
- `_signature` 参数：通过执行 sign.js 计算
- `a_bogus` 参数：通过执行 a_bogus.js 计算

这两个参数都需要通过Node.js环境执行相应的JavaScript代码来生成。

### 2. Protobuf协议

抖音直播消息使用Protobuf进行序列化，协议定义在 [protobuf/douyin.proto](protobuf/douyin.proto) 文件中。

如果需要更新协议定义，需要：
1. 修改 proto 文件
2. 使用 protoc 重新编译生成 Python 代码：
   ```bash
   protoc --python_betterproto_out=. douyin.proto
   ```

### 3. 多线程处理

由于涉及网络请求、WebSocket通信、GUI界面更新等多个并发任务，项目大量使用了多线程：
- GUI主线程：处理界面更新和用户交互
- 弹幕抓取线程：处理WebSocket连接和消息接收
- TTS播放线程：异步播放语音，避免阻塞主线程

### 4. 异常处理

考虑到网络不稳定等因素，各模块都应具有良好的异常处理机制，确保程序稳定运行。

## 代码规范

### 命名规范

- 类名使用大驼峰命名法（CamelCase）
- 函数和变量名使用小写字母，单词间用下划线分隔（snake_case）
- 常量使用全大写字母，单词间用下划线分隔

### 注释规范

- 类和重要函数需要有文档字符串说明用途和参数
- 复杂逻辑需要有行内注释解释
- 变量命名应尽量自解释，减少不必要的注释

### 代码组织

- 每个功能模块应尽量单一职责
- GUI相关的代码放在gui目录下
- 工具类函数可以放在单独的模块中

## 常见问题和解决方案

### 1. 签名失效

如果发现无法连接直播间，请检查：
1. sign.js 和 a_bogus.js 文件是否为最新版本
2. Node.js 环境是否正常
3. 网络请求参数是否发生变化

### 2. Protobuf解析错误

如果消息解析出现问题，请检查：
1. douyin.proto 文件是否与抖音协议一致
2. 是否需要更新协议定义并重新编译

### 3. GUI界面卡顿

如果GUI界面出现卡顿，请检查：
1. 是否在主线程中执行了耗时操作
2. TTS播放是否阻塞了主线程
3. 消息处理是否过于频繁

## 扩展开发

### 添加新的消息类型

1. 在 douyin.proto 中添加新的消息定义
2. 重新编译生成 Python 代码
3. 在 liveMan.py 中添加相应的消息处理逻辑
4. 在 GUI 中添加相应的显示逻辑

### 添加新的TTS触发条件

1. 在 TTSConfigDialog 中添加新的配置选项
2. 在 check_tts_trigger 方法中添加相应的判断逻辑
3. 在 tts_config.json 中添加相应的配置项

### 添加新的GUI功能

1. 在合适的标签页或新标签页中添加功能界面
2. 实现相应的业务逻辑
3. 注意多线程处理，避免阻塞GUI主线程