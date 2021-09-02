#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/8 下午6:39
# @Project : jd_scripts
# @File    : jx_factory_collect.py
# @Cron    : 45 */1 * * *
# @Desc    : 京喜App->我的->京喜工厂, 定时收电量
import aiohttp
from jx_factory import JxFactory
from utils.console import println
from utils.process import process_start
from utils.jx_init import jx_init


@jx_init
class JxFactoryCollect(JxFactory):
    """
    京喜工厂收电量
    """
    async def run(self):
        await self.get_encrypt()
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            success = await self.init(session)
            if not success:
                println('{}, 初始化失败!'.format(self.account))
                self.message = None
                return
            await self.collect_user_electricity(session)
            await self.collect_friend_electricity(session)


if __name__ == '__main__':
    process_start(JxFactoryCollect, '京喜工厂收电量', help=False)