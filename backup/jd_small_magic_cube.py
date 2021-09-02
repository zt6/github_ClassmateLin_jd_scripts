#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/26 9:13 上午
# @File    : jd_small_magic_cube.py
# @Project : jd_scripts
# @Cron    : 36 0 * * *
# @Desc    : 京东小魔方
import asyncio
import json

import aiohttp
from config import USER_AGENT
from urllib.parse import urlencode
from utils.jd_init import jd_init
from utils.console import println
from utils.logger import logger
from utils.process import process_start


@jd_init
class JdSmallMagicCube:
    """
    京东小魔方
    """
    headers = {
        'referer': 'https://h5.m.jd.com/babelDiy/AIIGSCTJLLOQCNCDZJHK/3ir78c82wkBTA4kwtuAUb3F1T5ej/index.html',
        'user-agent': USER_AGENT,
    }

    @logger.catch
    async def request(self, session, function_id, body=None, method='GET'):
        """
        请求数据
        :param function_id:
        :param body:
        :param method:
        :param session:
        :return:
        """
        try:
            if not body:
                body = {}

            params = {
                'functionId': function_id,
                'body': json.dumps(body),
                'appid': 'content_ecology',
                'client': 'wh5',
                'clientVersion': '10.1.2',
                'area': ''
            }

            url = 'https://api.m.jd.com/client.action?' + urlencode(params)
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)

            text = await response.text()

            data = json.loads(text)

            return data
        except Exception as e:
            println('{}, 请求服务器数据失败, {}'.format(self.account, e.args))
            return None

    @logger.catch
    async def do_tasks(self, session):
        """
        做任务
        :return:
        """
        data = await self.request(session, 'getInteractionInfo')
        if not data:
            println('{}, 获取任务列表失败!'.format(self.account))
            return
        interaction_id = data['result']['interactionId']
        shop_info = data['result']['shopInfoList']
        task_pool_info = data['result']['taskPoolInfo']
        task_pool_id = task_pool_info['taskPoolId']
        task_sku_list = data['result']['taskSkuInfo']

        for task in task_pool_info['taskList']:
            task_name = task['taskName']
            if task['taskStatus'] == 1:
                println('{}, 任务:{}已完成!'.format(self.account, task_name))
                continue
            if task['taskId'] == 7:
                for shop in shop_info:
                    res = await self.request(session, 'executeNewInteractionTask',
                                             {"interactionId": interaction_id, "shopId": shop['shopId'],
                                              "taskPoolId": task_pool_id, "taskType": task['taskId']})
                    println('{}, {}, {}'.format(self.account, task_name, res['result']['toast']))
                    await asyncio.sleep(2)

            elif task['taskId'] == 10:
                res = await self.request(session, 'executeNewInteractionTask',
                                         {"interactionId": interaction_id, "taskPoolId": task_pool_id,
                                          "taskType": task['taskId']})
                println('{}, {}, {}'.format(self.account, task_name, res['result']['toast']))
                await asyncio.sleep(2)

            elif task['taskId'] == 4:
                for sku in task_sku_list:
                    res = await self.request(session, 'executeNewInteractionTask', {
                        "sku": sku['skuId'],
                        "interactionId": interaction_id,
                        "taskPoolId": task_pool_id,
                        "taskType": task['taskId']})
                    println('{}, {}, {}'.format(self.account, task_name, res['result']['toast']))
                    await asyncio.sleep(2)

        for i in range(10):
            res = await self.request(session, 'getNewLotteryInfo', {"interactionId": interaction_id})

            println('{}, 抽奖结果:{}'.format(self.account, res))

            if res['result']['lotteryNum'] < 1:
                break

            await asyncio.sleep(2)

    @logger.catch
    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            await self.do_tasks(session)


if __name__ == '__main__':
    process_start(JdSmallMagicCube, '京东小魔方')
