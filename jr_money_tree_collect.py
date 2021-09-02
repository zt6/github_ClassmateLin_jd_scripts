#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/29 9:37 上午
# @File    : jr_money_tree_collect.py
# @Project : jd_scripts
# @Cron    : 35  */1 * * *
# @Desc    : 京东APP->我的->摇钱树, 定时收金果
import aiohttp
from utils.console import println
from jr_money_tree import JrMoneyTree
from utils.process import process_start


class JrMoneyTreeCollect(JrMoneyTree):
    """
    金果摇钱树收金果
    """
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self._cookies, headers=self.headers) as session:
            is_success = await self.login(session)
            if not is_success:
                println('{}, 登录失败, 退出程序...'.format(self.account))
            await self.harvest(session)  # 收金果


if __name__ == '__main__':
    process_start(JrMoneyTreeCollect, '金果摇钱树收金果', help=False)
