#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/7 下午11:14
# @Project : jd_scripts
# @File    : jd_health_collect.py
# @Cron    : 0 */30 * * *
# @Desc    : 京东APP->我的->签到领豆->边玩边赚->东东健康社区, 定时收能量
import aiohttp

from jd_health import JdHealth
from utils.process import process_start


class JdHealthCollect(JdHealth):
    """
    东东健康社区收能量
    """
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.collect_health_energy(session)


if __name__ == '__main__':
    process_start(JdHealthCollect, '东东健康社区收能量', help=False)
