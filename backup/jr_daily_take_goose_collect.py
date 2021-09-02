#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/29 9:29 上午
# @File    : jr_daily_take_goose_collect.py.py
# @Project : jd_scripts
# @Cron    : 17 */1 * * *
# @Desc    : 京东金融APP->天天提鹅， 定时收鹅蛋
import aiohttp
from jr_daily_take_goose import JrDailyTakeGoose


class JrDailyTakeGooseCollect(JrDailyTakeGoose):
    """
    天天提额收鹅蛋
    """
    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            await self.to_withdraw(session)


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JrDailyTakeGooseCollect, '天天提鹅收鹅蛋')
