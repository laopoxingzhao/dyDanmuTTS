# dyDanmuTTS - 抖音直播弹幕TTS语音合成系统

一个功能强大的抖音直播弹幕TTS（文本转语音）系统，支持实时弹幕语音播报、多种语音选择、智能配置管理等高级功能。

## 🎯 功能特性

### 🎵 核心功能
- **实时弹幕TTS**：将抖音直播间弹幕实时转换为语音播放
- **多种语音支持**：支持中文、粤语、英文的男女声共6种高质量语音
- **智能配置管理**：可视化配置界面，支持实时参数调整
- **高性能播放**：优化的音频播放器，支持播放间隔控制和状态监控
- **缓存机制**：智能音频缓存，提高重复内容的播放效率

### 🎤 语音选项
| 索引 | 语音名称 | 语言 | 性别 | Edge TTS名称 |
|------|----------|------|------|-------------|
| 0 | 晓晓 | 中文 | 女声 | zh-CN-XiaoxiaoNeural |
| 1 | 云希 | 中文 | 男声 | zh-CN-YunxiNeural |
| 2 | 曉儀 | 粤语 | 女声 | zh-HK-HiuGaaiNeural |
| 3 | 曉文 | 粤语 | 男声 | zh-HK-HiuMaanNeural |
| 4 | Jenny | 英文 | 女声 | en-US-JennyNeural |
| 5 | Guy | 英文 | 男声 | en-US-GuyNeural |

### ⚙️ 配置选项
- **音量控制**：0-100范围，自动转换为Edge TTS音量参数
- **语速调节**：0-20范围，支持-100%到+100%的语速调整
- **消息类型过滤**：可选择播报的消息类型（聊天、礼物、点赞等）
- **自定义模板**：支持进入房间、关注、礼物等事件的播报模板

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PyQt5
- edge-tts
- 其他依赖见 requirements.txt

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用

1. **启动主程序**
```bash
python optimized_main.py
```

2. **配置TTS设置**
- 在配置界面选择语音类型
- 调整音量和语速
- 选择要播报的消息类型

3. **开始直播弹幕TTS**
- 输入抖音直播间房间号
- 点击开始连接
- 系统将自动播报弹幕内容

## 📁 项目结构

```
dyDanmuTTS/
├── config/                 # 配置模块
│   ├── __init__.py
│   ├── app_config.json    # 应用配置文件
│   ├── config.py          # 配置管理器
│   └── log.py             # 日志管理器
├── dy_danmu/              # 抖音弹幕模块
│   ├── liveMan.py         # 直播间管理
│   ├── ac_signature.py     # 签名算法
│   └── protobuf/          # 协议解析
├── tts/                   # TTS语音合成模块
│   ├── optimized_tts_handler.py  # 优化的TTS处理器
│   └── tts_builder.py     # TTS构建器
├── tool/                  # 工具模块
│   ├── qt_audio_player.py  # Qt音频播放器
│   ├── memory_manager.py   # 内存管理器
│   └── optimized_queue.py  # 优化队列
├── ui/                    # 用户界面模块
│   ├── optimized_danmu_ui.py      # 弹幕UI
│   ├── tts_config_ui.py           # TTS配置UI
│   └── performance_monitor_ui.py  # 性能监控UI
├── tests/                 # 测试模块
│   ├── direct_tts_demo.py         # 直接TTS演示
│   ├── test_audio_player.py       # 音频播放器测试
│   ├── test_tts_generation.py     # TTS生成测试
│   └── test_voice_config.py       # 语音配置测试
├── output/                # 输出目录
│   ├── cache/            # 音频缓存
│   └── temp/             # 临时文件
├── log/                  # 日志目录
├── optimized_main.py     # 优化的主程序
└── README.MD            # 项目文档
```

## 🛠️ 配置说明

### 配置文件 (config/app_config.json)

```json
{
  "tts_settings": {
    "tts_enabled": true,           // 是否启用TTS
    "chat_tts": true,              // 聊天消息TTS
    "gift_tts": true,              // 礼物消息TTS
    "like_tts": true,              // 点赞消息TTS
    "voice": 1,                    // 语音选择 (0-5)
    "volume": 67,                  // 音量 (0-100)
    "speed": 8                     // 语速 (0-20)
  },
  "danmu_settings": {
    "WebcastChatMessage": true,    // 聊天消息
    "WebcastGiftMessage": true,    // 礼物消息
    "WebcastLikeMessage": true,    // 点赞消息
    "WebcastMemberMessage": true,  // 成员消息
    "WebcastSocialMessage": true   // 社交消息
  }
}
```

### 参数转换规则

**音量转换**：
- 配置值：0-100
- Edge TTS：-50% 到 +50%
- 50 = +0% (默认音量)
- 67 = +17% (示例配置)

**语速转换**：
- 配置值：0-20
- Edge TTS：-100% 到 +100%
- 10 = +0% (默认语速)
- 8 = -20% (示例配置)

## 🧪 测试工具

项目提供了完整的测试工具套件，位于 `tests/` 目录：

### 1. TTS生成测试
```bash
# 测试当前配置的TTS生成
python tests/direct_tts_demo.py demo

# 查看所有语音选项
python tests/direct_tts_demo.py info

# 对比不同语音效果
python tests/direct_tts_demo.py compare
```

### 2. 音频播放器测试
```bash
# 测试音频播放器功能
python tests/test_audio_player.py
```

### 3. TTS配置测试
```bash
# 测试不同语音配置
python tests/test_voice_config.py
```

### 4. 快速测试
```bash
# 快速功能测试
python tests/quick_test.py
```

## 📊 性能优化

### 播放器优化
- **智能等待机制**：从CPU密集型忙等待改为事件等待
- **播放间隔控制**：防止音频重叠，默认最小间隔0.5秒
- **状态监控**：实时跟踪播放状态和性能指标
- **错误恢复**：完善的异常处理和自动恢复机制

### 缓存机制
- **音频缓存**：重复内容直接使用缓存，提高响应速度
- **智能清理**：自动清理过期缓存，控制存储空间
- **命中率统计**：实时监控缓存效率

### 内存管理
- **队列优化**：高效的TTS任务队列管理
- **资源释放**：及时释放音频资源和内存
- **性能监控**：实时监控内存使用情况

## 🔧 高级功能

### 自定义播报模板

支持为不同事件设置自定义播报模板：

```json
{
  "enter_tts_templates": ["欢迎{user_name}进入直播间"],
  "follow_tts_templates": ["感谢{user_name}的关注"],
  "gift_tts_templates": ["感谢{user_name}送出的{gift_name}"],
  "keyword_reply_templates": {
    "1": ["你好啊{user_name}", "欢迎来到直播间{user_name}"],
    "问题": ["这是一个好问题", "让我想想怎么回答{user_name}"]
  }
}
```

### 关键词回复
- 设置特定关键词的自动回复
- 支持变量替换（用户名、礼物名等）
- 可配置多条回复随机选择

## 🐛 故障排除

### 常见问题

1. **TTS无法播放**
   - 检查网络连接
   - 确认edge-tts库正常安装
   - 查看日志文件获取详细错误信息

2. **音频质量问题**
   - 调整音量参数（建议50-80）
   - 检查语速设置（建议8-12）
   - 尝试不同的语音选项

3. **性能问题**
   - 启用音频缓存
   - 调整播放间隔
   - 关闭不必要的消息类型TTS

4. **配置不生效**
   - 检查配置文件格式
   - 确认权限设置
   - 重启应用程序

### 日志查看
日志文件位于 `log/app.log`，包含详细的运行信息和错误记录。

## 📈 性能指标

### 测试结果
- **音频生成速度**：平均1.8-2.5秒/条
- **文件大小**：10-40KB/条（取决于内容长度）
- **缓存命中率**：重复内容可达90%+
- **播放延迟**：<100ms（缓存命中时）

### 系统要求
- **内存**：建议512MB+
- **网络**：稳定的互联网连接（用于TTS服务）
- **存储**：建议1GB+（用于音频缓存）

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目。

### 开发环境设置
1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 运行测试：`python tests/quick_test.py`
4. 提交代码前确保所有测试通过

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- [edge-tts](https://github.com/rany2/edge-tts) - 微软Edge TTS接口
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [protobuf](https://developers.google.com/protocol-buffers) - 协议解析

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**：本工具仅供学习和个人使用，请遵守相关平台的使用条款和法律法规。