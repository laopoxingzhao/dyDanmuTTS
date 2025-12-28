#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试更新后的弹幕界面功能
"""

import sys
from PyQt5.QtWidgets import QApplication
from ui.danm_room_ui import Room

def test_updated_ui():
    """测试更新后的UI界面"""
    app = QApplication(sys.argv)
    
    # 创建界面
    window = Room()
    
    # 显示界面
    window.show()
    
    print("更新后的UI界面启动成功")
    print("新增功能测试：")
    print("  1. 检查所有消息类型复选框是否显示完整")
    print("  2. 切换到'TTS配置'标签页，检查TTS配置界面")
    print("  3. 测试TTS开关和各项设置")
    print("  4. 测试TTS模板设置功能")
    print("  5. 连接直播间后检查所有消息类型的显示")
    print("")
    print("支持的消息类型：")
    print("  - WebcastChatMessage (聊天消息)")
    print("  - WebcastGiftMessage (礼物消息)")
    print("  - WebcastLikeMessage (点赞消息)")
    print("  - WebcastMemberMessage (进入消息)")
    print("  - WebcastSocialMessage (关注消息)")
    print("  - WebcastFansclubMessage (粉丝团消息)")
    print("  - WebcastEmojiChatMessage (聊天表情包消息)")
    print("  - WebcastRoomStatsMessage (直播间统计信息)")
    print("  - WebcastRoomUserSeqMessage (直播间统计)")
    print("  - WebcastRoomMessage (直播间信息)")
    print("  - WebcastRoomRankMessage (直播间排行榜信息)")
    print("  - WebcastRoomStreamAdaptationMessage (直播间流配置)")
    
    return app.exec_()

if __name__ == '__main__':
    test_updated_ui()