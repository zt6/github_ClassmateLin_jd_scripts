#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/22 下午1:19
# @Project : jd_scripts
# @File    : jd_shop.py
# @Cron    : 1 0 * * *
# @Desc    : 京东APP首页->领京豆->进店领豆
import asyncio
import json
import urllib.parse

import aiohttp
from config import USER_AGENT
from utils.console import println
from utils.logger import logger
from utils.jd_init import jd_init


@jd_init
class JdShop:
    """
    进店领豆
    """
    headers = {
        'user-agent': USER_AGENT,
        'host': 'api.m.jd.com',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    @logger.catch
    async def request(self, session, function_id, body=None, method='GET'):
        """
        请求数据
        :param session:
        :param function_id:
        :param body:
        :param method:
        :return:
        """
        try:
            if not body:
                body = {}
            url = 'https://api.m.jd.com/client.action'
            params = {
                'functionId': function_id,
                'body': json.dumps(body),
                'appid': 'ld'
            }
            url = url + '?' + urllib.parse.urlencode(params)
            if method == 'GET':
                response = await session.get(url)
            else:
                response = await session.post(url)

            text = await response.text()
            data = json.loads(text)
            data['code'] = int(data['code'])
            return data
        except Exception as e:
            println('{}, 请求数据失败, {}!'.format(self.account, e.args))
            return {
                'code': 9999
            }

    @logger.catch
    async def do_tasks(self, session):
        """
        做任务
        :param session:
        :return:
        """
        res = await self.request(session, 'queryTaskIndex')
        if res.get('code') != 0:
            println('{}, 获取任务列表失败！'.format(self.account))
            return
        data = res.get('data')

        task_list = data.get('taskList', [])
        if not task_list:
            println('{}, {}'.format(self.account, data.get('taskErrorTips')))

        for task in task_list:
            if task['taskStatus'] == 3:
                println('{}, {}已拿到2京豆\n'.format(self.account, task.get('shopName')))
            else:
                res = await self.request(session, 'takeTask',  {'taskId': task['taskId']}, method='POST')
                if res.get('code') == 0:
                    println('{}, 成功完成任务!'.format(self.account))
                else:
                    println('{}, 无法完成任务!'.format(self.account))
                await asyncio.sleep(1)

    @logger.catch
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.do_tasks(session)


if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = JdShop(**JD_COOKIES[0])
    # asyncio.run(app.run())
    from utils.process import process_start
    process_start(JdShop, '进店领豆')