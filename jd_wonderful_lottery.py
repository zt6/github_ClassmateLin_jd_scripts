#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/27 10:56 上午
# @File    : jd_wonderful_lottery.py
# @Project : jd_scripts
# @Cron    : 44 4,5 * * *
# @Desc    : 京东APP->签到领豆->边玩边赚->每日抽奖
import asyncio
import json
import random
import re

import aiohttp
from urllib.parse import urlencode
from utils.jd_init import jd_init
from utils.console import println
from config import USER_AGENT
from db.model import Code
from utils.process import process_start

CODE_KEY = 'jd_wonderful_lottery'


def random_uuid():
    """
    :return:
    """
    s = '01234567890123456789'
    return ''.join(random.sample(s, 16)) + '-' + ''.join(random.sample(s, 16))


@jd_init
class JdWonderfulLottery:
    """
    京东精彩
    """
    headers = {
        'origin': 'https://jingcai-h5.jd.com',
        'user-agent': 'jdapp;' + USER_AGENT,
        'lop-dn': 'jingcai.jd.com',
        'accept': 'application/json, text/plain, */*',
        'appparams': '{"appid":158,"ticket_type":"m"}',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://jingcai-h5.jd.com/index.html'
    }

    activity_code = "1419494729103441920"

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

    async def do_tasks(self, session):
        """
        做任务
        :return:
        """
        res = await self.request(session, '/luckdraw/queryMissionList', [{
            "userNo": "$cooMrdGatewayUid$",
            "activity_code": self.activity_code
        }])
        if not res.get('success'):
            println('{}, 获取任务列表失败!'.format(self.account))
            return
        task_list = res['content']['missionList']

        for task in task_list:
            if task['status'] == 10:
                println('{}, 今日完成任务:{}!'.format(self.account, task['title']))
                continue

            if task['status'] == 11:
                for no in task['getRewardNos']:
                    body = [{
                        "activity_code": self.activity_code,
                        "userNo": "$cooMrdGatewayUid$",
                        "getCode": no
                    }]
                    res = await self.request(session, '/luckDraw/getDrawChance', body)
                    if res.get('success'):
                        println('{}, 成功领取一次抽奖机会!'.format(self.account))
                        break
                continue

            if '邀请' in task['title']:  # 邀请好友
                code = task['missionNo']
                println('{}, 助力码:{}'.format(self.account, code))
                Code.insert_code(code_val=code, code_key=CODE_KEY, sort=self.sort, account=self.account)
                continue

            for i in range(task['completeNum'], task['totalNum']):
                body = [{
                    "activity_code": self.activity_code,
                    "userNo": "$cooMrdGatewayUid$",
                    "missionNo": task['missionNo'],
                    "params": task['params']
                }]
                res = await self.request(session, '/luckDraw/completeMission', body)
                if res.get('success'):
                    println('{}, 完成任务:{}-{}'.format(self.account, task['title'], i + 1))
                await asyncio.sleep(1)

    async def run_help(self):
        """
        助力好友
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            item_list = Code.get_code_list(code_key=CODE_KEY)

            for item in item_list:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue
                res = await self.request(session, '/luckdraw/helpFriend', [{
                    "userNo": "$cooMrdGatewayUid$",
                    "missionNo": code
                }])
                if res.get('success'):
                    println('{}, 成功助力好友:{}'.format(self.account, account))
                else:
                    println('{}, 无法助力好友:{}'.format(self.account, account))

    async def lottery(self, session):
        """
        抽奖
        :return:
        """
        while True:
            res = await self.request(session, '/luckdraw/draw', [{
                "userNo": "$cooMrdGatewayUid$",
                "activity_code": self.activity_code
            }])
            if res.get('success'):
                println('{}, 抽奖成功'.format(self.account))
            else:
                break
            await asyncio.sleep(1)

    async def get_activate_code(self, session):
        """
        :return:
        """
        try:
            params = {
                'functionId': 'qryCompositeMaterials',
                'body': json.dumps({"qryParam": "[{\"type\":\"advertGroup\",\"id\":\"03744379\","
                                                "\"mapTo\":\"moreActivity\"},{\"type\":\"advertGroup\","
                                                "\"id\":\"04039687\",\"mapTo\":\"atmosphere\"},"
                                                "{\"type\":\"advertGroup\",\"id\":\"04030152\","
                                                "\"mapTo\":\"promotion\"},{\"type\":\"advertGroup\","
                                                "\"id\":\"04395256\",\"mapTo\":\"temporary\"}]",
                                    "activityId": "00360210", "pageId": "666370", "previewTime": "", "reqSrc": ""}),
                'client': 'wh5',
                'clientVersion': '1.0.0',
                'uuid': random_uuid()
            }
            url = 'https://api.m.jd.com/client.action?' + urlencode(params)
            response = await session.post(url=url)
            text = await response.text()
            data = json.loads(text)
            if data.get('code') != '0':
                return None
            item_list = data['data']['moreActivity']['list']
            for item in item_list:
                if '每日抽奖' in item['name']:
                    code = re.search('activityCode=(.*)&', item['link']).group(1)
                    return code
            return None
        except Exception as e:
            println('{}, 获取活动ID失败, {}'.format(self.account, e.args))
            return None

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            self.activity_code = await self.get_activate_code(session)
            if not self.activity_code:
                println('{}, 获取活动ID失败, 退出程序!'.format(self.account))
                return
            await self.do_tasks(session)  # 做任务
            await self.lottery(session)  # 抽奖


if __name__ == '__main__':
    process_start(JdWonderfulLottery, '精彩-每日抽奖', code_key=CODE_KEY)
