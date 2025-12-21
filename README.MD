
# 抖音网页版弹幕数据抓取

抖音网页版弹幕数据抓取来源于
https://github.com/saermart/DouyinLiveWebFetcher
### 环境：
- windows 10
- python 3.7+
- `protoc`版本：`libprotoc 25.1`
- NodeJs v18.2.0


## 功能特色

- ✅ 抓取直播间弹幕（聊天、点赞、礼物、关注、统计等消息）
- ✅ 解析Protobuf格式数据
- ✅ 自动计算signature和a_bogus参数
- ✅ 支持文字转语音(TTS)播放弹幕
# 抖音网页版弹幕数据抓取

抖音网页版弹幕数据抓取来源于 https://github.com/saermart/DouyinLiveWebFetcher

### 环境

- Windows 10 / Linux / macOS
- Python 3.8+
- `protoc` 版本（用于生成 protobuf）：libprotoc 25.1+
- 可选：Node.js（若使用 `PyExecJS` 执行 JavaScript）

详情请参阅 `ENVIRONMENT.md`。

## 功能特色

- ✅ 抓取直播间弹幕（聊天、点赞、礼物、关注、统计等消息）
- ✅ 解析 Protobuf 格式数据
- ✅ 自动计算 `signature` 和 `a_bogus` 参数
- ✅ 支持文字转语音 (TTS) 播放弹幕
- ✅ 支持播放 `video` 目录下的视频文件

## 抓取样例

```text
【进场msg】[79026102598][男]🌈尘埃🌈🌈 进入了直播间
【进场msg】[3548874980203464][男]姚先生 进入了直播间
【进场msg】[2594451873598365][女]王大锤锤锤 进入了直播间
【进场msg】[106602887532][男]嗨！ 进入了直播间
```

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 操作说明

- 按 `q` 键退出播放
- 按空格键暂停/继续播放

## 项目结构

有关项目的详细结构，请参阅 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 开发指南

有关如何进行二次开发和维护，请参阅 [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)

## 使用方式

### 命令行方式

```bash
# 直接运行，需要提供直播间ID
python main.py 50828500437

# 运行 GUI（示例）
python main.py gui
```

### GUI 方式

```bash
# 运行 GUI 主界面
python gui/main_gui.py

# 直接运行抖音弹幕抓取 GUI
python gui/douyin_gui.py
```

### TTS 方式

```bash
# 运行带 TTS 功能的命令行版本
python live_tts_main.py
```

## 配置说明

### TTS 配置

TTS 功能可以通过 `tts_config.json` 文件进行配置，也可以通过 GUI 界面的 TTS 配置面板进行配置。

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进项目。
