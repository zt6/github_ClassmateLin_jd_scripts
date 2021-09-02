#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/27 1:37 下午
# @File    : jd_polite.py
# @Project : jd_scripts
# @Cron    : 9 16 * * *
# @Desc    : 小鸽有礼
import asyncio
import json

import aiohttp

from utils.jd_init import jd_init
from utils.console import println
from config import USER_AGENT
from utils.process import process_start


@jd_init
class JdPolite:
    """
    小鸽有礼
    """
    headers = {
        'origin': 'https://jingcai-h5.jd.com',
        'user-agent': 'jdapp;' + USER_AGENT,
        'lop-dn': 'jingcai.jd.com',
        'accept': 'application/json, text/plain, */*',
        'appparams': '{"appid":158,"ticket_type":"m"}',
        'content-type': 'application/json',
        'referer': 'https://jingcai-h5.jd.com/index.html'
    }

    activityCode = "1410048365793640448"

    async def request(self, session, path, body=None, method='POST'):
        """
        请求服务器数据
        :return:
        """
        try:
            if not body:
                body = {}
            url = 'https://lop-proxy.jd.com/' + path
            if method == 'POST':
                response = await session.post(url, json=body)
            else:
                response = await session.get(url, json=body)

            text = await response.text()
            data = json.loads(text)
            return data

        except Exception as e:
            println('{}, 请求服务器数据失败, {}'.format(self.account, e.args))
            return {
                'success': False
            }

    async def do_tasks(self, session, times=3):
        """
        做任务
        :return:
        """
        if times < 0:
            return

        flag = False

        res = await self.request(session, '/WonderfulLuckDrawApi/queryMissionList', [{
            "userNo": "$cooMrdGatewayUid$",
            "activityCode": self.activityCode
        }])
        if not res.get('success'):
            println('{}, 获取任务列表失败!'.format(self.account))
            return
        task_list = res['content']['missionList']

        for task in task_list:
            if task['status'] == 10:
                println('{}, 今日完成任务:{}!'.format(self.account, task['title']))
                continue
            flag = True
            if task['status'] == 11:
                for no in task['getRewardNos']:
                    body = [{
                        "activityCode": self.activityCode,
                        "userNo": "$cooMrdGatewayUid$",
                        "getCode": no
                    }]
                    res = await self.request(session, '/WonderfulLuckDrawApi/getDrawChance', body)
                    if res.get('success'):
                        println('{}, 成功领取一次抽奖机会!'.format(self.account))
                        break
                    await asyncio.sleep(2)
                continue

            for i in range(task['completeNum'], task['totalNum']+1):
                body = {
                    "activityCode": self.activityCode,
                    "userNo": "$cooMrdGatewayUid$",
                    "missionNo": task['missionNo'],
                }
                if 'params' in task:
                    body['params'] = task['params']
                res = await self.request(session, '/WonderfulLuckDrawApi/completeMission', [body])
                if res.get('success'):
                    println('{}, 完成任务:{}-{}'.format(self.account, task['title'], i + 1))
                await asyncio.sleep(2.5)

        if flag:
            await self.do_tasks(session)

    async def lottery(self, session):
        """
        抽奖
        :return:
        """
        while True:
            res = await self.request(session, '/WonderfulLuckDrawApi/draw', [{
                "userNo": "$cooMrdGatewayUid$",
                "activityCode": self.activityCode
            }])
            if res.get('success'):
                println('{}, 抽奖成功'.format(self.account))
            else:
                break
            await asyncio.sleep(2)

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.do_tasks(session)
            await self.lottery(session)  # 抽奖


if __name__ == '__main__':
    process_start(JdPolite, '小鸽有礼')

