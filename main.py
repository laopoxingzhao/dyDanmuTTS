#!/usr/bin/python
# coding:utf-8


from liveMan import DouyinLiveWebFetcher

if __name__ == '__main__':
    
    live_id = '50828500437'
    room = DouyinLiveWebFetcher(live_id)
    # room.get_room_status() # 失效
    room.start()
