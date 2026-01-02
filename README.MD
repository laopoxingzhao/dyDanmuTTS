# dyDanmuTTS - 抖音直播弹幕监控系统

一个功能强大的抖音直播弹幕监控系统，支持实时弹幕捕获、消息类型过滤、可视化配置管理等高级功能。

## 🎯 功能特性

### 📊 核心功能
- **实时弹幕监控**：实时捕获和显示抖音直播间弹幕
- **多种消息类型**：支持聊天、礼物、点赞、进入、关注等多种消息类型
- **智能过滤**：按消息类型进行筛选，只显示感兴趣的内容
- **高性能捕获**：优化的弹幕捕获和显示机制
- **可视化配置**：友好的图形界面，支持实时参数调整

### 📋 消息类型支持
- **聊天消息** (WebcastChatMessage)：用户发送的弹幕内容
- **礼物消息** (WebcastGiftMessage)：用户送出的礼物信息
- **点赞消息** (WebcastLikeMessage)：用户的点赞行为
- **成员消息** (WebcastMemberMessage)：用户进入直播间
- **社交消息** (WebcastSocialMessage)：用户关注主播

### 🎙️ 事件播报功能
- **进入直播间播报**：欢迎新用户进入直播间
- **送礼播报**：播报用户送礼信息
- **关注播报**：感谢新关注用户
- **点赞播报**：播报点赞信息（可选）
- **自定义模板**：支持多种播报模板，随机选择
- **冷却控制**：防止播报过于频繁

### ⚙️ 配置选项
- **消息类型过滤**：可选择显示的消息类型
- **队列大小**：控制弹幕队列的最大长度
- **去重窗口**：设置消息去重的时间窗口
- **智能过滤**：启用智能去重和过滤功能
- **优先级处理**：按消息类型进行优先级排序

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PyQt5
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

2. **配置监控设置**
- 选择要显示的消息类型
- 调整队列大小和去重参数
- 启用智能过滤和优先级处理

3. **开始监控弹幕**
- 输入抖音直播间房间号
- 点击连接直播间
- 系统将自动显示弹幕内容

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
├── tool/                  # 工具模块
│   └── memory_manager.py   # 内存管理器
├── ui/                    # 用户界面模块
│   ├── optimized_danmu_ui.py      # 弹幕UI
│   ├── optimized_danmu_controller.py  # 弹幕控制器
│   └── room_input_ui.py             # 房间输入UI
├── output/                # 输出目录
├── log/                  # 日志目录
├── optimized_main.py     # 优化的主程序
└── README.MD            # 项目文档
```

## 🛠️ 配置说明

### 配置文件 (config/app_config.json)

```json
{
  "danmu_settings": {
    "WebcastChatMessage": true,    // 聊天消息
    "WebcastGiftMessage": true,    // 礼物消息
    "WebcastLikeMessage": true,    // 点赞消息
    "WebcastMemberMessage": true,  // 成员消息
    "WebcastSocialMessage": true   // 社交消息
  },
  "tts_settings": {
    "enabled": true,
    "event_announcement": {
      "member_enter": {
        "enabled": true,
        "cooldown": 30,
        "priority": 5,
        "user_cooldown": true,
        "templates": [
          "欢迎 {user_name} 进入直播间",
          "{user_name} 来了，欢迎欢迎",
          "欢迎 {user_name} 来到直播间"
        ]
      },
      "gift_send": {
        "enabled": true,
        "cooldown": 5,
        "priority": 7,
        "enable_cooldown": false,
        "min_gift_count": 1,
        "templates": [
          "感谢 {user_name} 送出的 {gift_name} {gift_count} 个",
          "感谢 {user_name} 的 {gift_name} x{gift_count}",
          "{user_name} 送了 {gift_name} {gift_count} 个，感谢支持"
        ]
      },
      "social_follow": {
        "enabled": true,
        "cooldown": 60,
        "priority": 6,
        "user_cooldown": true,
        "templates": [
          "感谢 {user_name} 的关注",
          "欢迎 {user_name} 关注主播",
          "{user_name} 关注了，感谢支持"
        ]
      },
      "like": {
        "enabled": false,
        "cooldown": 10,
        "priority": 4,
        "enable_cooldown": true,
        "min_like_count": 10,
        "templates": [
          "{user_name} 点了 {count} 个赞",
          "感谢 {user_name} 的 {count} 个赞"
        ]
      }
    }
  }
}
```

### 配置参数说明

**消息类型设置**：
- `WebcastChatMessage`：是否显示聊天消息
- `WebcastGiftMessage`：是否显示礼物消息
- `WebcastLikeMessage`：是否显示点赞消息
- `WebcastMemberMessage`：是否显示成员进入消息
- `WebcastSocialMessage`：是否显示关注消息

**事件播报设置**：

1. **进入直播间播报 (member_enter)**
   - `enabled`：是否启用进入播报
   - `cooldown`：播报冷却时间（秒）
   - `priority`：播报优先级（0-10，越高越优先）
   - `user_cooldown`：是否启用用户级冷却（同一用户冷却）
   - `templates`：播报模板列表（支持变量：{user_name}, {gender}, {time}）

2. **送礼播报 (gift_send)**
   - `enabled`：是否启用送礼播报
   - `cooldown`：播报冷却时间（秒）
   - `priority`：播报优先级
   - `enable_cooldown`：是否启用冷却
   - `min_gift_count`：最小礼物数量阈值
   - `templates`：播报模板列表（支持变量：{user_name}, {gift_name}, {gift_count}, {time}）

3. **关注播报 (social_follow)**
   - `enabled`：是否启用关注播报
   - `cooldown`：播报冷却时间（秒）
   - `priority`：播报优先级
   - `user_cooldown`：是否启用用户级冷却
   - `templates`：播报模板列表（支持变量：{user_name}, {time}）

4. **点赞播报 (like)**
   - `enabled`：是否启用点赞播报（默认关闭）
   - `cooldown`：播报冷却时间（秒）
   - `priority`：播报优先级
   - `enable_cooldown`：是否启用冷却
   - `min_like_count`：最小点赞数量阈值
   - `templates`：播报模板列表（支持变量：{user_name}, {count}, {time}）

### 事件播报使用示例

1. **启用进入直播间播报**
   - 在配置文件中设置 `"member_enter.enabled": true`
   - 自定义播报模板，例如："欢迎 {user_name} 进入直播间"
   - 设置冷却时间，避免频繁播报（建议30秒）

2. **配置送礼播报**
   - 设置 `"gift_send.enabled": true`
   - 设置最小礼物数量阈值，例如只播报1个以上的礼物
   - 可以关闭用户冷却，确保每次送礼都播报
   - 设置较高的优先级（如7），确保送礼消息优先播放

3. **感谢关注用户**
   - 启用 `"social_follow.enabled": true`
   - 设置较长的冷却时间（如60秒），避免重复感谢
   - 使用多种模板增加变化

4. **播报模板变量说明**
   - `{user_name}`：用户昵称
   - `{gender}`：用户性别（男/女/未知）
   - `{gift_name}`：礼物名称
   - `{gift_count}`：礼物数量
   - `{count}`：点赞数量
   - `{time}`：当前时间

5. **播报优先级建议**
   - 送礼消息：7-10（最高优先级）
   - 关注消息：6-8（高优先级）
   - 进入消息：4-6（中等优先级）
   - 点赞消息：3-5（低优先级）

## 📊 界面说明

### 主界面
- **直播间ID输入**：输入要监控的抖音直播间ID
- **连接/断开按钮**：控制与直播间的连接状态
- **性能状态**：显示当前系统性能状态

### 弹幕监控标签页
- **消息类型筛选**：左侧面板，勾选要显示的消息类型
- **快速过滤设置**：
  - 启用智能过滤：智能去重重复消息
  - 启用优先级处理：按消息类型排序
- **队列设置**：
  - 队列大小：控制弹幕列表最大长度（5-100）
  - 去重窗口：消息去重时间窗口（5-300秒）
- **弹幕列表**：右侧面板，实时显示弹幕内容
- **统计信息**：显示总计和过滤的消息数量

### 高级设置标签页
- **系统统计**：
  - 运行时间
  - 总消息数
  - 过滤消息数
  - 消息速率

## 🔧 高级功能

### 智能过滤
系统提供智能过滤功能，可以：
- 自动去重相似消息
- 按时间窗口过滤重复内容
- 提高消息显示质量

### 优先级处理
支持按消息类型进行优先级排序：
- 聊天消息：中等优先级
- 礼物消息：高优先级
- 关注消息：高优先级
- 进入消息：低优先级
- 点赞消息：低优先级

### 队列管理
- 控制弹幕列表的最大长度
- 自动清理旧消息
- 保持界面流畅

## 🐛 故障排除

### 常见问题

1. **无法连接直播间**
   - 检查网络连接
   - 确认直播间ID正确
   - 查看日志文件获取详细错误信息

2. **弹幕显示延迟**
   - 检查网络速度
   - 调整队列大小
   - 启用智能过滤

3. **性能问题**
   - 减少显示的消息类型
   - 调整队列大小
   - 启用智能过滤

4. **配置不生效**
   - 检查配置文件格式
   - 确认权限设置
   - 重启应用程序

### 日志查看
日志文件位于 `log/app.log`，包含详细的运行信息和错误记录。

## 📈 性能优化

### 显示优化
- **智能滚动**：自动滚动到最新消息
- **列表限制**：控制最大显示条数
- **颜色区分**：不同消息类型使用不同颜色

### 过滤优化
- **类型过滤**：快速过滤不需要的消息类型
- **智能去重**：自动过滤重复内容
- **优先级排序**：重要消息优先显示

### 内存优化
- **队列管理**：高效的弹幕队列管理
- **自动清理**：及时清理过期消息
- **性能监控**：实时监控系统性能

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目。

### 开发环境设置
1. 克隆项目
2. 安装依赖：`pip install -r requirements.txt`
3. 运行程序：`python optimized_main.py`
4. 提交代码前确保功能正常

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [protobuf](https://developers.google.com/protocol-buffers) - 协议解析

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**：本工具仅供学习和个人使用，请遵守相关平台的使用条款和法律法规。