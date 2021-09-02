#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/31 下午9:22
# @Project : jd_scripts
# @File    : jd_planting_bean_collect.py
# @Cron    : 40 */2 * * *
# @Desc    : 京东APP->我的->签到领豆->种豆得豆, 定时收取营养液
import aiohttp

from utils.console import println
from utils.process import process_start
from jd_planting_bean import JdPlantingBean


class JdPlantingBeanCollect(JdPlantingBean):
    """
    种豆得豆收营养夜
    """
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            self.message = None
            is_success = await self.planting_bean_index(session)
            if not is_success:
                println('{}, 无法获取活动数据!'.format(self.account))
                return
            await self.receive_nutrient(session)
            await self.collect_nutriments(session)
            self.message = None


if __name__ == '__main__':
    process_start(JdPlantingBeanCollect, '种豆得豆收营养液', help=False)
