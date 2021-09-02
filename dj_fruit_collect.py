#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/27 下午8:28 
# @File    : dj_fruit_collect.py
# @Project : jd_scripts
# @Cron    : 42 */1 * * *
# @Desc    : 京东APP->京东到家->免费水果, 定时领水滴/浇水
import aiohttp
from dj_fruit import DjFruit
from utils.console import println
from utils.process import process_start

from config import DJ_FRUIT_KEEP_WATER


class DjFruitCollect(DjFruit):

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            dj_cookies = await self.login(session)
            if not dj_cookies:
                return
            println('{}, 登录成功...'.format(self.account))

        async with aiohttp.ClientSession(cookies=dj_cookies, headers=self.headers) as session:
            await self.receive_water_wheel(session)  # 领取水车水滴
            await self.watering(session, keep_water=DJ_FRUIT_KEEP_WATER)


if __name__ == '__main__':
    process_start(DjFruitCollect, '到家果园领水滴')
