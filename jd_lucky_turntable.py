#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/19 10:30
# @File    : jd_lucky_turntable.py
# @Project : jd_scripts
# @Cron    : 10 10,23 * * *
# @Desc    : 幸运大转盘, 入口忘了在哪
import asyncio
import json
import re
from urllib.parse import quote, unquote

import aiohttp

from utils.logger import logger
from utils.console import println
from utils.jd_init import jd_init
from config import USER_AGENT


@jd_init
class JdLuckyTurntable:
    headers = {
        'user-agent': USER_AGENT,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3',
        'x-requested-with': 'com.jingdong.app.mall',
        'Sec-Fetch-Mode': 'navigate',
        'referer': 'https://pro.m.jd.com/mall/active/3ryu78eKuLyY5YipWWVSeRQEpLQP/index.html?forceCurrentView=1'
    }

    result = []
    message = None

    async def get_task_list(self, session):
        """
        :param session:
        :return:
        """
        url = 'https://pro.m.jd.com/mall/active/3ryu78eKuLyY5YipWWVSeRQEpLQP/index.html?forceCurrentView=1'
        try:
            response = await session.get(url)
            text = await response.text()
            pattern = r'window.__react_data__ = (\{.*\})'

            temp = re.findall(pattern, text)

            task_list = []

            if len(temp) == 0:
                println('账号:{}, 匹配活动数据失败!'.format(self.account))
                return False

            data = json.loads(temp[0])
            if 'activityData' not in data or 'floorList' not in data['activityData']:
                return task_list

            for line in data['activityData']['floorList']:
                if 'template' in line and line['template'] == 'score_task':
                    task_list = line['taskItemList']

            return task_list

        except Exception as e:
            logger.info(e.args)

    async def do_task(self, session, en_award_k):
        """
        做任务
        :param session:
        :param en_award_k:
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=babelDoScoreTask'
        params = {"enAwardK": en_award_k, "isQueryResult": 0, "siteClient": "apple", "mitemAddrId": "",
                  "geo": {"lng": "", "lat": ""}, "addressId": "", "posLng": "", "posLat": "", "homeLng": "",
                  "homeLat": "", "focus": "", "innerAnchor": "", "cv": "2.0"}
        session.headers.add('content-type', 'application/x-www-form-urlencoded')
        body = 'body={}&client=wh5&clientVersion=1.0.0'.format(quote(json.dumps(params)))

        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)

            if data['code'] == '0':
                self.result.append('{}, 当前积分:{}, 任务进度: {}'.format(data['promptMsg'],
                                                                  data['userScore'], data['taskProgress']))
                println('账号:{}, {}, 当前积分:{}, 任务进度: {}'.format(self.account, data['promptMsg'],
                                                              data['userScore'], data['taskProgress']))
                return data['userScore']
            else:
                println('账号:{}, 做任务失败, {}'.format(self.account, data))
        except Exception as e:
            logger.error('账号:{}, 做任务异常:{}'.format(self.account, e.args))

    async def lottery(self, session):
        """
        抽奖  a84f9428da0bb36a6a11884c54300582
        :param session:
        :return:
        """
        session.headers.add('origin', 'https://h5.m.jd.com')
        session.headers.add('referer', 'https://h5.m.jd.com/')
        session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
        home_url = 'https://pro.m.jd.com/mall/active/3ryu78eKuLyY5YipWWVSeRQEpLQP/index.html?forceCurrentView=1'
        lottery_url = 'https://api.m.jd.com/client.action?functionId=babelGetLottery'
        try:
            response = await session.get(home_url)
            text = await response.text()
            temp = re.findall(r'window.__react_data__ = (\{.*\})', text)
            if len(temp) == 0:
                println('账号:{}, 匹配活动数据失败!'.format(self.account))
                return False
            data = json.loads(temp[0])
            if 'activityData' not in data or 'floorList' not in data['activityData']:
                println('账号:{}, 匹配活动数据失败!'.format(self.account))
                return False

            user_score = 0
            en_award_k = None

            for line in data['activityData']['floorList']:
                if 'template' in line and line['template'] == 'choujiang_wheel':
                    user_score = line['lotteryGuaGuaLe']['userScore']
                    en_award_k = line['lotteryGuaGuaLe']['enAwardK']

            if user_score < 80:
                println('账号: {}, 积分:{}, 不够抽奖...'.format(self.account, user_score))
                self.result.append('积分:{}, 不够抽奖...'.format(user_score))
                return False

            if not en_award_k:
                println('账号: {}, 查找抽奖数据失败, 无法抽奖'.format(self.account))
                return False

            params = {
                'enAwardK': en_award_k,
                'authType': '2'
            }
            body = 'body={}&client=wh5&clientVersion=1.0.0'.format(quote(json.dumps(params)))
            response = await session.post(url=lottery_url, data=body)
            text = await response.text()
            data = json.loads(text)

            if data['code'] != '0':
                self.result.append('账号:{} 抽奖失败:{}'.format(self.account, data))
                println('抽奖失败:{}'.format(self.account, data))
                return False
            else:
                if 'prizeName' in data:
                    self.result.append('抽奖成功:{}'.format(data['promptMsg'], data['prizeName']))
                    println('账号:{}, 抽奖成功:{}'.format(self.account, data['promptMsg'], data['prizeName']))
                else:
                    println('账号:{}, 抽奖成功:{}'.format(self.account, data['promptMsg']))
                    self.result.append('抽奖成功:{}'.format(data['promptMsg']))
                println('账号:{}, 当前剩余积分:{}'.format(self.account, data['userScore']))
                self.result.append('当前剩余积分:{}'.format(data['userScore']))

            await self.lottery(session)

        except Exception as e:
            println(e.args)

    async def run(self):
        """
        入口函数
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            task_list = await self.get_task_list(session)

            for j in range(len(task_list)):
                task = task_list[j]
                println('账号: {}, 任务:{}, 进度:{}...'.format(self.account, task['flexibleData']['taskName'],
                                                         task['flexibleData']['taskProgress']))

                if task['joinTimes'] == task['taskLimit']:
                    self.result.append('任务:{}, 进度:{}...'.format(task['flexibleData']['taskName'],
                                                                task['flexibleData']['taskProgress']))

                for i in range(task['joinTimes'], task['taskLimit']):
                    println('账号: {}, 去完成{}, 第{}次!'.format(self.account, task['flexibleData']['taskName'], i + 1))
                    en_award_k = task['enAwardK']
                    await self.do_task(session, en_award_k)

            await self.lottery(session)  # 抽奖


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdLuckyTurntable, name='幸运大转盘')
