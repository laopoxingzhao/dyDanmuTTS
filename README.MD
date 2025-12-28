# dyDanmuTTS - 抖音直播弹幕TTS系统

## 📖 简介

dyDanmuTTS是一个专为抖音直播设计的弹幕文本转语音（TTS）系统，支持实时弹幕抓取、智能过滤、优先级处理和高质量语音播放。

## ✨ 核心功能

### 🎯 弹幕抓取
- 实时抓取抖音直播间弹幕消息
- 支持多种消息类型（聊天、礼物、关注、点赞等）
- 稳定的连接和自动重连机制

### 🤖 智能TTS处理
- **高质量语音合成**：基于Microsoft Edge TTS引擎
- **多种语音选择**：支持中文、英文、粤语等多种语音
- **智能去重过滤**：避免重复消息的频繁播放
- **优先级队列**：礼物和重要消息优先播放
- **音频缓存**：重复内容直接使用缓存，提升响应速度

### 🔊 音频播放优化
- **Qt音频引擎**：基于Qt多媒体框架的稳定播放
- **播放间隔控制**：防止音频重叠和播放过快
- **音量动态调节**：支持实时音量调整
- **播放状态监控**：详细的播放统计和状态跟踪
- **错误恢复**：完善的异常处理和自动恢复

### 📊 性能监控
- **实时统计**：播放成功率、缓存命中率等指标
- **内存管理**：智能临时文件管理和内存优化
- **性能分析**：详细的性能报告和优化建议

## 🚀 快速开始

### 1. 环境要求

```bash
# Python 3.8+
pip install PyQt5 edge-tts asyncio threading queue

# 可选：更好的性能
pip install psutil
```

### 2. 基本使用

#### GUI模式（推荐）
```bash
python optimized_main.py gui
```

#### 命令行模式
```bash
python optimized_main.py <房间ID>
```

### 3. 配置说明

系统配置文件位于 `config/app_config.json`：

```json
{
  "tts_settings": {
    "tts_enabled": true,
    "voice": 0,
    "speed": 10,
    "volume": 50,
    "chat_tts": true,
    "gift_tts": true,
    "like_tts": false
  },
  "danmu_settings": {
    "WebcastChatMessage": true,
    "WebcastGiftMessage": true,
    "WebcastLikeMessage": false
  }
}
```

## 🎛️ 语音配置

### 支持的语音类型
- `0`: zh-CN-XiaoxiaoNeural (女声，默认)
- `1`: zh-CN-YunxiNeural (男声)
- `2`: zh-HK-HiuGaaiNeural (粤语女声)
- `3`: zh-HK-HiuMaanNeural (粤语男声)
- `4`: en-US-JennyNeural (英文女声)
- `5`: en-US-GuyNeural (英文男声)

### 语速和音量调节
- **语速范围**: 1-20，10为正常速度
- **音量范围**: 0-100，50为正常音量

## 🔧 高级功能

### 智能消息过滤

系统内置智能过滤机制：

1. **去重过滤**：相同内容30秒内只播放一次
2. **无意义消息**：过滤纯表情、数字、符号等
3. **相似模式**：识别相似模式的消息避免重复
4. **优先级处理**：
   - 礼物消息：最高优先级
   - 关注消息：高优先级
   - 进入消息：中等优先级
   - 普通聊天：普通优先级

### 音频缓存系统

- **缓存位置**: `output/cache/`
- **缓存策略**: LRU算法，最多缓存50个文件
- **缓存键**: 基于内容+语音+语速+音量的哈希值
- **自动清理**: 超出限制时自动清理最旧文件

### 性能优化特性

1. **异步处理**：TTS生成和播放异步进行
2. **预加载机制**：提前加载常用音频内容
3. **播放间隔控制**：最小间隔0.5秒，防止重叠
4. **内存管理**：智能临时文件清理和内存监控
5. **错误恢复**：完善的异常处理和自动重试

## 📈 监控和统计

### 实时统计指标

```python
# 获取TTS处理器统计
stats = tts_handler.get_stats()
print(f"总播放数: {stats['total_played']}")
print(f"缓存命中率: {stats['cache_hit_rate']:.2%}")
print(f"平均生成时间: {stats['avg_generation_time']:.2f}s")

# 获取音频播放器统计
player_stats = audio_player.get_stats()
print(f"播放成功率: {player_stats['success_rate']:.2%}")
print(f"平均播放时长: {player_stats['average_duration']:.2f}s")
```

### 性能监控界面

GUI版本提供实时性能监控界面：
- 📊 实时播放统计
- 💾 内存使用情况
- 🎵 音频缓存状态
- ⚡ 系统性能指标

## 🧪 测试工具

### 音频播放器测试
```bash
python test_audio_player.py player    # 测试音频播放器
python quick_test.py                # 快速功能测试
```

### TTS生成测试
```bash
python test_tts_generation.py direct    # 直接TTS测试
python test_tts_generation.py handler   # 完整TTS处理器测试
python test_tts_generation.py generate  # 仅音频生成测试
```

## 🔍 故障排除

### 常见问题

1. **TTS不工作**
   - 检查网络连接（edge-tts需要网络）
   - 确认tts_enabled设置为true
   - 查看日志文件排查错误

2. **音频无法播放**
   - 确认系统音频设备正常
   - 检查音量设置
   - 验证音频文件权限

3. **性能问题**
   - 调整队列大小限制
   - 启用智能过滤减少处理量
   - 清理音频缓存释放空间

### 日志分析

日志文件位置：`log/`
```bash
# 查看最新日志
tail -f log/dyDanmuTTS_$(date +%Y%m%d).log

# 搜索错误
grep "ERROR" log/dyDanmuTTS_*.log
```

## 📁 项目结构

```
dyDanmuTTS/
├── config/           # 配置文件和日志系统
├── dy_danmu/        # 抖音弹幕抓取模块
├── tts/            # TTS处理和音频生成
├── tool/           # 工具模块（音频播放、内存管理等）
├── ui/             # 用户界面
├── output/          # 输出文件（缓存、临时文件等）
├── log/            # 日志文件
└── test_*.py       # 测试脚本
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境搭建
```bash
git clone <repository>
cd dyDanmuTTS
pip install -r requirements.txt
python optimized_main.py gui
```

### 代码规范
- 使用Python 3.8+语法
- 遵循PEP 8编码规范
- 添加适当的注释和文档
- 编写单元测试

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- [edge-tts](https://github.com/rany2/edge-tts) - Microsoft Edge TTS接口
- PyQt5 - 跨平台GUI框架
- 所有贡献者和用户的支持

---

**🎉 感谢使用dyDanmuTTS！如有问题请提交Issue或联系开发者。**