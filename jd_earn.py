#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/17 下午9:38
# @Project : jd_scripts
# @File    : jd_earn.py
# @Cron    : 10 10 * * *
# @Desc    : 微信小程序->京东赚赚
import asyncio
from urllib.parse import urlencode
import aiohttp
import ujson

from config import USER_AGENT
from utils.process import process_start
from utils.console import println
from utils.jd_init import jd_init


@jd_init
class JdEarn:
    total_gold = 0  # 总金币
    cash_ratio = 10000  # 提现比例

    headers = {
        'referer': 'https://servicewechat.com/wx8830763b00c18ac3/96/page-frame.html',
        'wqreferer': 'http://wq.jd.com/wxapp/pages/hd-interaction/task/index',
        'user-agent': USER_AGENT.replace('jdapp;', ''),
        'content-type': 'application/json'
    }

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
            params = {
                'functionId': function_id,
                'body': body,
                'client': 'wh5',
                'clientVersion': '9.1.0',
            }
            url = 'https://api.m.jd.com/client.action?' + urlencode(params)
            if method == 'GET':
                response = await session.get(url=url, json=body)
            else:
                response = await session.post(url=url, json=body)
            data = await response.json()
            data['code'] = int(data.get('code', -1))
            return data
        except Exception as e:
            println('{}, 请求服务器失败, {}'.format(self.account, e.args))
            return {
                'code': -1
            }

    async def get_task_list(self, session):
        """
        :return:
        """
        res = await self.request(session, 'interactTaskIndex', {"mpVersion": "3.4.0"})
        if res.get('code') != 0:
            println('{}, 获取数据失败!'.format(self.account))
            return False
        data = res.get('data', None)
        if not data:
            return False
        self.total_gold = int(data.get('totalNum', '0'))
        return data['taskDetailResList']

    async def do_tasks(self, session, task_list):
        """
        做任务
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            if task['status'] == 2:
                println('{}, 任务:《{}》今日已完成!'.format(self.account, task['taskName']))
                continue

            body = {"taskId": task['taskId'], "mpVersion": "3.4.0"}
            if task.get('itemId', None):
                body['itemId'] = task['itemId']

            res = await self.request(session, 'doInteractTask', body)
            if res.get('code') == 0:
                println('{}, 成功完成任务:《{}》!'.format(self.account, task['taskName']))
            else:
                print('{}, 无法完成任务:《{}》!'.format(self.account, task['taskName']))

            await asyncio.sleep(2)

    async def notify(self, session):
        # 刷新金币数据
        await self.get_task_list(session)
        self.message = '【活动名称】京东赚赚\n【活动入口】微信小程序-京东赚赚\n' \
                       '【京东账号】{}\n【金币总数】{}\n【可提现金额】{}￥\n' \
                       ''.format(self.account, self.total_gold, round(self.total_gold / self.cash_ratio, 2))

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:
            task_list = await self.get_task_list(session)
            if not task_list:
                println('{}, 无法获取活动数据, 退出程序!'.format(self.account))
                return
            await self.do_tasks(session, task_list)
            #await self.notify(session)


if __name__ == '__main__':
    process_start(JdEarn, '京东赚赚')
