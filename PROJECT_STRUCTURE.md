# 项目结构说明

## 总体架构

本项目用于抓取抖音网页版直播间的实时弹幕数据，主要包括以下几个部分：

```
dyDanmuTTS/
├── main.py                      # 命令行入口点
├── live_tts_main.py             # TTS主程序
├── requirements.txt             # Python依赖包列表
├── PROJECT_STRUCTURE.md         # 本文件
├── README.MD                   # 项目说明文档
├── core/                       # 核心功能模块
│   ├── __init__.py
│   ├── live_manager.py         # 核心直播弹幕抓取类
│   ├── message_handler.py      # 消息处理队列
│   └── signature/              # 签名计算相关文件
│       ├── __init__.py
│       ├── ac_signature.py     # 签名计算辅助类
│       └── js/                 # JavaScript签名文件
│           ├── sign.js
│           ├── a_bogus.js
│           ├── webmssdk.js
│           └── sign_v0.js
├── protobuf/                   # Protobuf相关文件
│   ├── douyin.proto            # 抖音消息协议定义
│   ├── douyin.py               # 编译后的Python代码
│   └── protoc.exe              # Protobuf编译器
├── tts/                        # 文字转语音模块
│   ├── __init__.py
│   └── play_audio_async.py     # 异步音频播放实现
├── ui/                         # GUI界面相关文件
│   ├── __init__.py
│   ├── main_gui.py             # GUI入口点示例
│   └── douyin_gui.py           # 抖音直播弹幕获取GUI主程序
├── config/                     # 配置文件
│   ├── __init__.py
│   └── tts_config.json         # TTS配置文件
└── utils/                      # 工具函数
    ├── __init__.py
    └── play_audio.py           # 音频播放功能
```

## 核心组件详解

### core/ - 核心功能模块

这是项目的核心模块，负责连接抖音直播间、获取弹幕数据和解析Protobuf消息。

#### core/live_manager.py

这是项目的核心模块，负责：
1. 通过JS计算请求参数签名
2. 发起HTTP请求获取直播信息
3. 建立WebSocket连接接收弹幕数据
4. 解析Protobuf格式的消息
5. 分发不同类型的消息

#### core/message_handler.py

实现了消息队列机制：
- 提供线程安全的消息存取接口
- 控制消息队列的最大容量
- 防止内存溢出

#### core/signature/ - 签名计算模块

抖音为了防止爬虫，对接口进行了签名保护，包括：
- `_signature` 参数：通过执行 sign.js 计算
- `a_bogus` 参数：通过执行 a_bogus.js 计算

这两个参数都需要通过Node.js环境执行相应的JavaScript代码来生成。

### protobuf/ - 协议处理

抖音直播消息使用Protobuf进行序列化，协议定义在 [protobuf/douyin.proto](protobuf/douyin.proto) 文件中。

如果需要更新协议定义，需要：
1. 修改 proto 文件
2. 使用 protoc 重新编译生成 Python 代码：
   ```bash
   protoc --python_betterproto_out=. douyin.proto
   ```

### tts/ - 文字转语音模块

#### tts/play_audio_async.py

基于Edge TTS的异步音频播放实现，使用pygame播放音频。

### ui/ - 图形界面模块

#### ui/douyin_gui.py

完整功能的GUI程序，包括：
- 直播间连接管理
- 弹幕消息显示和过滤
- TTS语音播报配置和播放
- 实时统计数据展示

#### ui/main_gui.py

项目主入口GUI，提供功能选择界面。

### config/ - 配置文件

#### config/tts_config.json

TTS功能的配置文件，可以通过GUI界面进行配置。

### utils/ - 工具函数

#### utils/play_audio.py

音频播放工具函数。

## 开发注意事项

### 1. 多线程处理

项目使用多线程处理不同任务，避免阻塞主线程：
- 弹幕监听线程
- TTS播放线程
- 心跳包发送线程

### 2. 异常处理

各个模块都有完善的异常处理机制，确保程序稳定运行。

### 3. 资源管理

合理管理系统资源，特别是音频播放资源，避免资源泄露。
