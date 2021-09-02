#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/24 3:56 下午
# @File    : jx_pasture_collect.py
# @Project : jd_scripts
# @Cron    : 40 */2 * * *
# @Desc    : 京喜APP->京喜牧场->定时收金币/割草/投喂小鸡
import aiohttp
from utils.console import println
from jx_pasture import JxPasture


class JxPastureCollect(JxPasture):

    async def run(self):
        """
        :return:
        """
        await self.get_encrypt()
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            if not await self.init(session):
                println('{}, 无法初始化, 退出程序!'.format(self.account))
                return

            await self.get_gold_from_bull(session)  # 收牛牛金币
            await self.buy_food(session) # 买白菜
            await self.feed(session)  # 喂白菜
            await self.mowing(session, max_times=10)  # 割草
            await self.sweep_chicken_legs(session, max_times=10)  # 扫鸡腿


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JxPastureCollect, '京喜牧场', help=False)
