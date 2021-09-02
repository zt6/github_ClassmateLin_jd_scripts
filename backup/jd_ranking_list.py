#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/21 9:58 上午
# @File    : jd_ranking_list.py
# @Project : jd_scripts
# @Cron    : 21 9 * * *
# @Desc    : 今日王牌, 入口忘了在哪。
import asyncio
import json

import aiohttp
from urllib.parse import unquote
from utils.console import println
from utils.logger import logger
from utils.jd_init import jd_init
from utils.process import process_start


@jd_init
class JdRankingList:
    """
    今日王牌
    """

    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://h5.m.jd.com/babelDiy/Zeus/3wtN2MjeQgjmxYTLB3YFcHjKiUJj/index.html',
        'Host': 'api.m.jd.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-cn'
    }

    async def query_task(self, session):
        """
        查询任务
        :return:
        """
        task_list = []

        url = 'https://api.m.jd.com/client.action?functionId=queryTrumpTask&body=%7B%22sign%22%3A2%7D&appid' \
              '=content_ecology&clientVersion=9.2.0&client=wh5'
        try:
            response = await session.post(url)
            text = await response.text()
            data = json.loads(text)
            await asyncio.sleep(1)
            if data['code'] != '0':
                println('{}, 获取任务列表失败...'.format(self.account))
            else:
                task_list = data['result']['taskList']
                task_list.append(data['result']['signTask'])
                println('{}, 查询任务成功！'.format(self.account))
        except Exception as e:
            logger.error('{}, 查询任务失败:{}'.format(self.account, e.args))

        return task_list

    async def do_task(self, session, task):
        """
        做任务
        :param session:
        :param task:
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=doTrumpTask&body' \
              '=%7B%22taskId%22%3A{}%2C%22itemId%22%3A%22{}%22%2C%22sign%22%3A2%7D&appid' \
              '=content_ecology&clientVersion=9.2.0' \
              '&client=wh5'.format(task['taskId'], task['taskItemInfo']['itemId'])
        try:
            response = await session.post(url)
            text = await response.text()
            data = json.loads(text)
            if data['code'] != '0':
                logger.info('{}, 做任务失败:{}'.format(self.account, data))
            else:

                println('{}, 完成任务:{}, {}'.format(self.account, task['taskName'],
                                                 data['result']['lotteryMsg'].replace('\n', '')))

        except Exception as e:
            logger.error('{}, 做任务失败: {}'.format(self.account, e.args))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            task_list = await self.query_task(session)
            for task in task_list:
                await self.do_task(session, task)
                await asyncio.sleep(1)


if __name__ == '__main__':
    process_start(JdRankingList, '今日王牌')

