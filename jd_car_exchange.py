#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/18 3:11 下午
# @File    : jd_car_exchange.py
# @Project : jd_scripts
# @Cron    : 0 0 * * *
# @Desc    : 京东汽车兑换
import aiohttp
import ujson

from jd_car import JdCar
from utils.process import process_start
from utils.console import println


class JdCarExchange(JdCar):
    """
    兑换京豆
    """
    async def exchange(self, session):
        """
        兑换
        :param session:
        :return:
        """
        res = await self.request(session, 'v1/user/exchange/bean', method='POST')
        println('{}, 兑换结果:{}'.format(self.account, res))

    async def run(self):
        """
        请求数据
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:
            await self.exchange(session)


if __name__ == '__main__':
    process_start(JdCarExchange, '京东汽车兑换')
