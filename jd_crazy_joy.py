#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/18 11:50 上午
# @File    : jd_crazy_joy.py
# @Project : jd_scripts
# @Desc    : 京东APP-签到领豆-疯狂的JOY
import asyncio
import hashlib
import time
from urllib.parse import urlencode, quote

import aiohttp
import json
import random
from config import USER_AGENT
from utils.jd_init import jd_init
from utils.jx_init import md5
from utils.logger import logger
from utils.process import process_start
from utils.console import println


def get_uts(t):
    """
    :return:
    """
    t = str(int(time.time() * 1000))
    e = '1670115333'
    e = t[-8:] + e + t
    return e


@jd_init
class JdCrazyJoy:
    headers = {
        'referer': 'https://crazy-joy.jd.com/',
        'origin': 'https://crazy-joy.jd.com',
        'user-agent': USER_AGENT,
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }

    async def request(self, session, function_id, body=None, method='GET'):
        """
        请求数据
        :param method:
        :param body:
        :param function_id:
        :param session:
        :return:
        """
        try:
            t = str(int(time.time()) * 1000)
            params = {
                'uts': get_uts(t),
                't': t,
                'appid': 'crazy_joy',
                'functionId': function_id,
            }
            if body:
                params['body'] = json.dumps(body)
            url = 'https://api.m.jd.com?' + urlencode(params)
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)
            data = await response.json()

            return data
        except Exception as e:
            println('{}, 请求数据失败, {}!'.format(self.account, e.args))

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            data = await self.request(session, 'crazyJoy_joy_trade', {"action": "BUY", "joyId": "28", "boxId": ""})
            println(data)


if __name__ == '__main__':
    from config import JD_COOKIES

    app = JdCrazyJoy(**JD_COOKIES[0])
    asyncio.run(app.run())
