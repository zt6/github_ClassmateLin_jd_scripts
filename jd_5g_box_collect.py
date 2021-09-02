#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 下午8:51
# @Project : jd_scripts
# @File    : jd_5g_box_collect.py
# @Cron    : 27 */3 * * *
# @Desc    :  京东APP->营业厅->领京豆, 5G盲盒每3小时收取信号值
import aiohttp
from utils.logger import logger
from utils.process import process_start
from jd_5g_box import Jd5GBox


class Jd5GBoxCollect(Jd5GBox):
    """
    5G盲合收信号
    """
    @logger.catch
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.get_coin(session)  # 收取信号值


process_start(Jd5GBoxCollect, '5G盲合-收信号', help=False)
