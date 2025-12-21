#!/usr/bin/python
# coding:utf-8

import codecs
import gzip
import hashlib
import random
import re
import string
import subprocess
import threading
import time
import execjs
import urllib.parse
from contextlib import contextmanager
from unittest.mock import patch

import requests
import websocket
from py_mini_racer import MiniRacer
import logging

from core.signature.ac_signature import get__ac_signature
from protobuf.douyin import *

from urllib3.util.url import parse_url
from core.message_handler import MessageHandler


logger = logging.getLogger(__name__)


def execute_js(js_file: str):
    """
    执行 JavaScript 文件
    :param js_file: JavaScript 文件路径
    :return: 执行结果
    """
    with open(js_file, 'r', encoding='utf-8') as file:
        js_code = file.read()
    
    ctx = execjs.compile(js_code)
    return ctx


@contextmanager
def patched_popen_encoding(encoding='utf-8'):
    original_popen_init = subprocess.Popen.__init__
    
    def new_popen_init(self, *args, **kwargs):
        kwargs['encoding'] = encoding
        original_popen_init(self, *args, **kwargs)
    
    with patch.object(subprocess.Popen, '__init__', new_popen_init):
        yield


def generateSignature(wss, script_file='core/signature/js/sign.js'):
    """
    出现gbk编码问题则修改 python模块subprocess.py的源码中Popen类的__init__函数参数encoding值为 "utf-8"
    """
    params = ("live_id,aid,version_code,webcast_sdk_version,"
              "room_id,sub_room_id,sub_channel_id,did_rule,"
              "user_unique_id,device_platform,device_type,ac,"
              "identity").split(',')
    wss_params = urllib.parse.urlparse(wss).query.split('&')
    wss_maps = {i.split('=')[0]: i.split("=")[-1] for i in wss_params}
    tpl_params = [f"{i}={wss_maps.get(i, '')}" for i in params]
    param = ','.join(tpl_params)
    md5 = hashlib.md5()
    md5.update(param.encode())
    md5_param = md5.hexdigest()
    
    with codecs.open(script_file, 'r', encoding='utf8') as f:
        script = f.read()
    
    ctx = MiniRacer()
    ctx.eval(script)
    
    try:
        signature = ctx.call("get_sign", md5_param)
        return signature
    except Exception as e:
        logger.exception("generateSignature 调用 get_sign 失败")
    
    # 以下代码对应js脚本为sign_v0.js
    # context = execjs.compile(script)
    # with patched_popen_encoding(encoding='utf-8'):
    #     ret = context.call('getSign', {'X-MS-STUB': md5_param})
    # return ret.get('X-Bogus')


def generateMsToken(length=182):
    """
    产生请求头部cookie中的msToken字段，其实为随机的107位字符
    :param length:字符位数
    :return:msToken
    """
    random_str = ''
    base_str = string.ascii_letters + string.digits + '-_'
    _len = len(base_str) - 1
    for _ in range(length):
        random_str += base_str[random.randint(0, _len)]
    return random_str


class DouyinLiveWebFetcher:
    
    def __init__(self, live_id, abogus_file='core/signature/js/a_bogus.js'):  # 可根据实际需求调整路径
        """
        直播间弹幕抓取对象
        :param live_id: 直播间的直播id，打开直播间web首页的链接如：https://live.douyin.com/261378947940，
                        其中的261378947940即是live_id
        :param abogus_file: a_bogus生成所用的JS文件路径
        """
        self.abogus_file = abogus_file
        self.__ttwid = None
        self.__room_id = None
        self.session = requests.Session()
        self.live_id = live_id
        self.host = "https://www.douyin.com/"
        self.live_url = "https://live.douyin.com/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
        self.headers = {
            'User-Agent': self.user_agent
        }
        self.message_handler = MessageHandler()
        self.on_status_update = None  # 状态更新回调函数
        # 控制心跳线程和安全关闭
        self._heartbeat_stop_event = threading.Event()
        self._heartbeat_thread = None
    
    def start(self):
        self._connectWebSocket()
    
    def stop(self):
        """
        安全停止：关闭心跳线程、WebSocket 和消息处理器
        """
        try:
            # 停止心跳线程
            self._heartbeat_stop_event.set()

            # 关闭 websocket（如果存在）
            if hasattr(self, 'ws') and self.ws is not None:
                try:
                    self.ws.close()
                except Exception:
                    logger.exception("关闭 WebSocket 时发生错误")

            # 停止消息处理器
            try:
                self.message_handler.stop()
            except Exception:
                logger.exception("停止 message_handler 时发生错误")

            # 等待心跳线程退出
            if self._heartbeat_thread is not None and self._heartbeat_thread.is_alive():
                self._heartbeat_thread.join(timeout=2)
        except Exception:
            logger.exception("停止 DouyinLiveWebFetcher 时发生未处理的错误")
    
    def get_message(self, timeout=None):
        """
        获取一条消息
        :param timeout: 超时时间（秒），None表示阻塞等待
        :return: 消息字典或None（超时或被关闭时）
        """
        return self.message_handler.get_message(timeout)
    
    def get_message_nowait(self):
        """
        非阻塞获取一条消息
        :return: 消息字典或None（无消息时）
        """
        return self.message_handler.get_message_nowait()
    
    def message_queue_size(self):
        """
        获取当前消息队列中的消息数量
        :return: 消息数量
        """
        return self.message_handler.size()
    
    @property
    def ttwid(self):
        """
        产生请求头部cookie中的ttwid字段，访问抖音网页版直播间首页可以获取到响应cookie中的ttwid
        :return: ttwid
        """
        if self.__ttwid:
            return self.__ttwid
        headers = {
            "User-Agent": self.user_agent,
        }
        try:
            response = self.session.get(self.live_url, headers=headers)
            response.raise_for_status()
        except Exception as err:
            logger.error("Request the live url error: %s", err)
        else:
            self.__ttwid = response.cookies.get('ttwid')
            return self.__ttwid
    
    @property
    def room_id(self):
        """
        根据直播间的地址获取到真正的直播间roomId，有时会有错误，可以重试请求解决
        :return:room_id
        """
        if self.__room_id:
            return self.__room_id
        url = self.live_url + self.live_id
        headers = {
            "User-Agent": self.user_agent,
            "cookie": f"ttwid={self.ttwid}&msToken={generateMsToken()}; __ac_nonce=0123407cc00a9e438deb4",
        }
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
        except Exception as err:
            logger.error("Request the live room url error: %s", err)
        else:
            match = re.search(r'roomId\\":\\"(\d+)\\"', response.text)
            if match is None or len(match.groups()) < 1:
                logger.error("No match found for roomId in response")
            
            self.__room_id = match.group(1)
            
            return self.__room_id
    
    def get_ac_nonce(self):
        """
        获取 __ac_nonce
        """
        resp_cookies = self.session.get(self.host, headers=self.headers).cookies
        return resp_cookies.get("__ac_nonce")
    
    def get_ac_signature(self, __ac_nonce: str = None) -> str:
        """
        获取 __ac_signature
        """
        __ac_signature = get__ac_signature(self.host[8:], __ac_nonce, self.user_agent)
        self.session.cookies.set("__ac_signature", __ac_signature)
        return __ac_signature
    
    def get_a_bogus(self, url_params: dict):
        """
        获取 a_bogus
        """
        url = urllib.parse.urlencode(url_params)
        ctx = execute_js(self.abogus_file)
        _a_bogus = ctx.call("get_ab", url, self.user_agent)
        return _a_bogus
    
    def get_room_status(self):
        """
        获取直播间开播状态:
        room_status: 2 直播已结束
        room_status: 0 直播进行中
        """
        msToken = generateMsToken()
        nonce = self.get_ac_nonce()
        signature = self.get_ac_signature(nonce)
        url = ('https://live.douyin.com/webcast/room/web/enter/?aid=6383'
               '&app_name=douyin_web&live_id=1&device_platform=web&language=zh-CN&enter_from=page_refresh'
               '&cookie_enabled=true&screen_width=5120&screen_height=1440&browser_language=zh-CN&browser_platform=Win32'
               '&browser_name=Edge&browser_version=140.0.0.0'
               f'&web_rid={self.live_id}'
               f'&room_id_str={self.room_id}'
               '&enter_source=&is_need_double_stream=false&insert_task_id=&live_reason=&msToken=' + msToken)
        query = parse_url(url).query
        params = {i[0]: i[1] for i in [j.split('=') for j in query.split('&')]}
        a_bogus = self.get_a_bogus(params)  # 计算a_bogus,成功率不是100%，出现失败时重试即可
        url += f"&a_bogus={a_bogus}"
        headers = self.headers.copy()
        headers.update({
            'Referer': f'https://live.douyin.com/{self.live_id}',
            'Cookie': f'ttwid={self.ttwid};__ac_nonce={nonce}; __ac_signature={signature}',
        })
        resp = self.session.get(url, headers=headers)
        try:
            data = resp.json().get('data')
        except requests.exceptions.JSONDecodeError:
            logger.error("无法解析房间状态响应为JSON格式，响应内容: %s", resp.text[:200])
            return
            
        if data:
            room_status = data.get('room_status')
            user = data.get('user')
            user_id = user.get('id_str')
            nickname = user.get('nickname')
            logger.info("直播间状态 - %s [%s]: %s", nickname, user_id, ['正在直播', '已结束'][bool(room_status)])
    
    def _connectWebSocket(self):
        """
        连接抖音直播间websocket服务器，请求直播间数据
        """
        wss = ("wss://webcast100-ws-web-lq.douyin.com/webcast/im/push/v2/?app_name=douyin_web"
               "&version_code=180800&webcast_sdk_version=1.0.14-beta.0"
               "&update_version_code=1.0.14-beta.0&compress=gzip&device_platform=web&cookie_enabled=true"
               "&screen_width=1536&screen_height=864&browser_language=zh-CN&browser_platform=Win32"
               "&browser_name=Mozilla"
               "&browser_version=5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,"
               "%20like%20Gecko)%20Chrome/126.0.0.0%20Safari/537.36"
               "&browser_online=true&tz_name=Asia/Shanghai"
               "&cursor=d-1_u-1_fh-7392091211001140287_t-1721106114633_r-1"
               f"&internal_ext=internal_src:dim|wss_push_room_id:{self.room_id}|wss_push_did:7319483754668557238"
               f"|first_req_ms:1721106114541|fetch_time:1721106114633|seq:1|wss_info:0-1721106114633-0-0|"
               f"wrds_v:7392094459690748497"
               f"&host=https://live.douyin.com&aid=6383&live_id=1&did_rule=3&endpoint=live_pc&support_wrds=1"
               f"&user_unique_id=7319483754668557238&im_path=/webcast/im/fetch/&identity=audience"
               f"&need_persist_msg_count=15&insert_task_id=&live_reason=&room_id={self.room_id}&heartbeatDuration=0")
        
        signature = generateSignature(wss)
        wss += f"&signature={signature}"
        
        headers = {
            "cookie": f"ttwid={self.ttwid}",
            'user-agent': self.user_agent,
        }
        self.ws = websocket.WebSocketApp(wss,
                                         header=headers,
                                         on_open=self._wsOnOpen,
                                         on_message=self._wsOnMessage,
                                         on_error=self._wsOnError,
                                         on_close=self._wsOnClose)
        try:
            self.ws.run_forever()
        except Exception:
            self.stop()
            raise
    
    def _sendHeartbeat(self):
        """
        发送心跳包
        """
        while not self._heartbeat_stop_event.is_set():
            try:
                heartbeat = PushFrame(payload_type='hb').SerializeToString()
                if hasattr(self, 'ws') and self.ws is not None:
                    self.ws.send(heartbeat, websocket.ABNF.OPCODE_PING)
                    logger.debug("发送心跳包")
            except Exception:
                logger.exception("心跳包发送错误")
                # 发生错误时尝试退出心跳循环
                self._heartbeat_stop_event.set()
                break
            time.sleep(5)
    
    def _wsOnOpen(self, ws):
        """
        连接建立成功
        """
        logger.info("WebSocket 连接成功.")
        if self.on_status_update:
            self.on_status_update("WebSocket连接成功")
        # 清理停止标志并以 daemon 线程启动心跳
        self._heartbeat_stop_event.clear()
        self._heartbeat_thread = threading.Thread(target=self._sendHeartbeat, daemon=True)
        self._heartbeat_thread.start()
    
    def _wsOnMessage(self, ws, message):
        """
        接收到数据
        :param ws: websocket实例
        :param message: 数据
        """
        
        # 根据proto结构体解析对象
        package = PushFrame().parse(message)
        response = Response().parse(gzip.decompress(package.payload))
        
        # 返回直播间服务器链接存活确认消息，便于持续获取数据
        if response.need_ack:
            ack = PushFrame(log_id=package.log_id,
                            payload_type='ack',
                            payload=response.internal_ext.encode('utf-8')
                            ).SerializeToString()
            ws.send(ack, websocket.ABNF.OPCODE_BINARY)
        
        # 根据消息类别解析消息体
        for msg in response.messages_list:
            method = msg.method
            try:
                {
                    'WebcastChatMessage': self._parseChatMsg,  # 聊天消息
                    'WebcastGiftMessage': self._parseGiftMsg,  # 礼物消息
                    'WebcastLikeMessage': self._parseLikeMsg,  # 点赞消息
                    'WebcastMemberMessage': self._parseMemberMsg,  # 进入直播间消息
                    'WebcastSocialMessage': self._parseSocialMsg,  # 关注消息
                    'WebcastRoomUserSeqMessage': self._parseRoomUserSeqMsg,  # 直播间统计
                    'WebcastFansclubMessage': self._parseFansclubMsg,  # 粉丝团消息
                    'WebcastControlMessage': self._parseControlMsg,  # 直播间状态消息
                    'WebcastEmojiChatMessage': self._parseEmojiChatMsg,  # 聊天表情包消息
                    'WebcastRoomStatsMessage': self._parseRoomStatsMsg,  # 直播间统计信息
                    'WebcastRoomMessage': self._parseRoomMsg,  # 直播间信息
                    'WebcastRoomRankMessage': self._parseRankMsg,  # 直播间排行榜信息
                    'WebcastRoomStreamAdaptationMessage': self._parseRoomStreamAdaptationMsg,  # 直播间流配置
                }.get(method)(msg.payload)
            except Exception:
                pass
    
    def _wsOnError(self, ws, error):
        logger.error("WebSocket 错误: %s", error)
        if self.on_status_update:
            self.on_status_update(f"WebSocket错误: {error}")
    
    def _wsOnClose(self, ws, *args):
        try:
            self.get_room_status()
        except Exception:
            logger.exception("获取房间状态时出错")
        logger.info("WebSocket 连接已关闭")
        if self.on_status_update:
            self.on_status_update("WebSocket连接已关闭")
    
    def _parseChatMsg(self, payload):
        """聊天消息"""
        message = ChatMessage().parse(payload)
        user_name = message.user.nick_name
        user_id = message.user.id
        content = message.content
        
        chat_msg = {
            'user_name': user_name,
            'user_id': user_id,
            'content': content
        }
        
        self.message_handler.add_message('chat', chat_msg)
        logger.info("聊天消息 [%s] %s: %s", user_id, user_name, content)

    
    def _parseGiftMsg(self, payload):
        """礼物消息"""
        message = GiftMessage().parse(payload)
        user_name = message.user.nick_name
        gift_name = message.gift.name
        gift_cnt = message.combo_count
        
        gift_msg = {
            'user_name': user_name,
            'gift_name': gift_name,
            'gift_count': gift_cnt
        }
        
        self.message_handler.add_message('gift', gift_msg)
        # print(f"【礼物msg】{user_name} 送出了 {gift_name}x{gift_cnt}")
    
    def _parseLikeMsg(self, payload):
        '''点赞消息'''
        message = LikeMessage().parse(payload)
        user_name = message.user.nick_name
        count = message.count
        
        like_msg = {
            'user_name': user_name,
            'count': count
        }
        
        self.message_handler.add_message('like', like_msg)
        # print(f"【点赞msg】{user_name} 点了{count}个赞")
    
    def _parseMemberMsg(self, payload):
        '''进入直播间消息'''
        message = MemberMessage().parse(payload)
        user_name = message.user.nick_name
        user_id = message.user.id
        gender = ["女", "男"][message.user.gender]
        
        member_msg = {
            'user_name': user_name,
            'user_id': user_id,
            'gender': gender
        }
        
        self.message_handler.add_message('member', member_msg)
        # print(f"【进场msg】[{user_id}][{gender}]{user_name} 进入了直播间")
    
    def _parseSocialMsg(self, payload):
        '''关注消息'''
        message = SocialMessage().parse(payload)
        user_name = message.user.nick_name
        user_id = message.user.id
        
        social_msg = {
            'user_name': user_name,
            'user_id': user_id
        }
        
        self.message_handler.add_message('social', social_msg)
        # print(f"【关注msg】[{user_id}]{user_name} 关注了主播")
    
    def _parseRoomUserSeqMsg(self, payload):
        '''直播间统计'''
        message = RoomUserSeqMessage().parse(payload)
        current = message.total
        total = message.total_pv_for_anchor
        
        stats_msg = {
            'current_viewers': current,
            'total_viewers': total
        }
        
        self.message_handler.add_message('room_stats', stats_msg)
        # print(f"【统计msg】当前观看人数: {current}, 累计观看人数: {total}")
    
    def _parseFansclubMsg(self, payload):
        '''粉丝团消息'''
        message = FansclubMessage().parse(payload)
        content = message.content
        
        fansclub_msg = {
            'content': content
        }
        
        self.message_handler.add_message('fansclub', fansclub_msg)
        # print(f"【粉丝团msg】 {content}")
    
    def _parseEmojiChatMsg(self, payload):
        '''聊天表情包消息'''
        message = EmojiChatMessage().parse(payload)
        emoji_id = message.emoji_id
        user = message.user
        common = message.common
        default_content = message.default_content
        
        emoji_msg = {
            'emoji_id': emoji_id,
            'user': user,
            'common': common,
            'default_content': default_content
        }
        
        self.message_handler.add_message('emoji_chat', emoji_msg)
        logger.debug("聊天表情包 id=%s user=%s common=%s default=%s", emoji_id, user, common, default_content)
    
    def _parseRoomMsg(self, payload):
        message = RoomMessage().parse(payload)
        common = message.common
        room_id = common.room_id
        
        room_msg = {
            'room_id': room_id
        }
        
        self.message_handler.add_message('room', room_msg)
        logger.debug("直播间消息 room_id=%s", room_id)
    
    def _parseRoomStatsMsg(self, payload):
        message = RoomStatsMessage().parse(payload)
        display_long = message.display_long
        
        room_stats_msg = {
            'display_info': display_long
        }
        
        self.message_handler.add_message('room_display_stats', room_stats_msg)
        logger.debug("直播间统计: %s", display_long)
    
    def _parseRankMsg(self, payload):
        message = RoomRankMessage().parse(payload)
        ranks_list = message.ranks_list
        
        rank_msg = {
            'ranks': ranks_list
        }
        
        self.message_handler.add_message('rank', rank_msg)
        # print(f"【直播间排行榜msg】{ranks_list}")
    
    def _parseControlMsg(self, payload):
        '''直播间状态消息'''
        message = ControlMessage().parse(payload)
        
        control_msg = {
            'status': message.status
        }
        
        self.message_handler.add_message('control', control_msg)
        
        if message.status == 3:
            logger.info("直播间已结束 (status=3)")
            self.stop()
    
    def _parseRoomStreamAdaptationMsg(self, payload):
        message = RoomStreamAdaptationMessage().parse(payload)
        adaptationType = message.adaptation_type
        
        adaptation_msg = {
            'adaptation_type': adaptationType
        }
        
        self.message_handler.add_message('stream_adaptation', adaptation_msg)
        logger.info('直播间 adaptation: %s', adaptationType)