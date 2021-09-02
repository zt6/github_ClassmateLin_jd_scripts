#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/13 11:58 上午
# @File    : jd_good_morning.py
# @Project : jd_scripts
# @Cron    : 30 6 * * *
# @Desc    : 京东APP首页->领京豆->早起福利
import aiohttp
import json
from utils.console import println
from utils.logger import logger
from utils.jd_init import jd_init
from config import USER_AGENT


@jd_init
class JdGoodMorning:

    headers = {
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': USER_AGENT,
        'Accept-Language': 'zh-Hans-CN;q=1',
        'Host': 'api.m.jd.com'
    }

    @logger.catch
    async def run(self):
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            url = 'https://api.m.jd.com/client.action?functionId=morningGetBean&area=22_1930_50948_52157&body=%7B%22rnVersion%22%3A%224.7%22%2C%22fp%22%3A%22-1%22%2C%22eid%22%3A%22%22%2C%22shshshfp%22%3A%22-1%22%2C%22userAgent%22%3A%22-1%22%2C%22shshshfpa%22%3A%22-1%22%2C%22referUrl%22%3A%22-1%22%2C%22jda%22%3A%22-1%22%7D&build=167724&client=apple&clientVersion=10.0.6&d_brand=apple&d_model=iPhone12%2C8&eid=eidI1aaf8122bas5nupxDQcTRriWjt7Slv2RSJ7qcn6zrB99mPt31yO9nye2dnwJ/OW%2BUUpYt6I0VSTk7xGpxEHp6sM62VYWXroGATSgQLrUZ4QHLjQw&isBackground=N&joycious=60&lang=zh_CN&networkType=wifi&networklibtype=JDNetworkBaseAF&openudid=32280b23f8a48084816d8a6c577c6573c162c174&osVersion=14.4&partner=apple&rfs=0000&scope=01&screen=750%2A1334&sign=0c19e5962cea97520c1ef9a2e67dda60&st=1625354180413&sv=112&uemps=0-0&uts=0f31TVRjBSsqndu4/jgUPz6uymy50MQJSPYvHJMKdY9TUw/AQc1o/DLA/rOTDwEjG4Ar9s7IY4H6IPf3pAz7rkIVtEeW7XkXSOXGvEtHspPvqFlAueK%2B9dfB7ZbI91M9YYXBBk66bejZnH/W/xDy/aPsq2X3k4dUMOkS4j5GHKOGQO3o2U1rhx5O70ZrLaRm7Jy/DxCjm%2BdyfXX8v8rwKw%3D%3D&uuid=hjudwgohxzVu96krv/T6Hg%3D%3D&wifiBssid=c99b216a4acd3bce759e369eaeeafd7'
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            println('{}, 早起福利执行结果:{}'.format(self.account, data))


if __name__ == '__main__':

    from utils.process import process_start
    process_start(JdGoodMorning, '早起福利')
