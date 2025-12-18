# 项目结构说明

## 总体架构

本项目用于抓取抖音网页版直播间的实时弹幕数据，主要包括以下几个部分：

```
DouyinLiveWebFetcher/
├── main.py                      # 命令行入口点
├── liveMan.py                   # 核心直播弹幕抓取类
├── ac_signature.py              # 签名计算辅助类
├── message_handler.py           # 消息处理队列
├── play_audio.py                # 音频播放功能
├── live_tts_main.py             # TTS主程序
├── tts_config.json              # TTS配置文件
├── sign.js                      # 签名计算JavaScript文件
├── a_bogus.js                   # a_bogus参数计算JavaScript文件
├── webmssdk.js                  # WebSocket相关JavaScript文件
├── requirements.txt             # Python依赖包列表
├── PROJECT_STRUCTURE.md         # 本文件
├── README.MD                    # 项目说明文档
├── gui/                         # GUI界面相关文件
│   ├── main_gui.py              # GUI入口点示例
│   └── douyin_gui.py            # 抖音直播弹幕获取GUI主程序
├── edgetts/                     # TTS相关文件
│   ├── play_audio_async.py      # 异步音频播放实现
│   └── __init__.py              
├── protobuf/                    # Protobuf相关文件
│   ├── douyin.proto             # 抖音消息协议定义
│   ├── douyin.py                # 编译后的Python代码
│   └── protoc.exe               # Protobuf编译器
└── video/                       # 视频播放相关文件
    └── video.mp4                # 示例视频文件
```

## 核心组件详解

### 1. 弹幕抓取核心 (liveMan.py)

这是整个项目的核心，负责：
- 计算请求参数签名
- 建立与抖音服务器的WebSocket连接
- 解析Protobuf格式的消息
- 分发不同类型的消息

### 2. 消息处理 (message_handler.py)

实现了消息队列机制：
- 统一处理各种类型的直播消息
- 提供线程安全的消息存取接口
- 控制消息队列的最大容量

### 3. 图形界面 (gui/)

提供了图形化操作界面：
- douyin_gui.py: 功能完整的GUI程序，支持多种消息类型显示和TTS功能
- main_gui.py: 简单的GUI示例程序

### 4. 文本转语音 (edgetts/)

基于Edge TTS实现的文本朗读功能：
- play_audio_async.py: 异步播放TTS音频
- 与GUI集成实现实时弹幕朗读

### 5. 协议解析 (protobuf/)

使用Protobuf解析抖音直播协议：
- douyin.proto: 协议定义文件
- douyin.py: 自动生成的Python类

## 运行方式

### 命令行方式
```bash
python main.py <room_id>
```

### GUI方式
```bash
python gui/main_gui.py     # 简易GUI示例
python gui/douyin_gui.py   # 完整功能GUI
```

### TTS方式
```bash
python live_tts_main.py
```

## 配置文件

### tts_config.json
TTS功能的配置文件，可以配置：
- 各类消息的TTS开关
- TTS播报模板
- 关键词触发规则

## 依赖关系

所有依赖包在requirements.txt中定义，使用以下命令安装：
```bash
pip install -r requirements.txt
```

另外需要安装Node.js环境以执行JavaScript签名计算。