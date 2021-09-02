#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/18 2:20 下午
# @File    : jd_car.py
# @Cron    : 10 7 * * *
# @Project : jd_scripts
# @Desc    : 京东汽车
import ujson
import time
import json
import aiohttp
from urllib.parse import urlencode
import asyncio
from utils.jd_init import jd_init
from utils.console import println
from utils.logger import logger
from utils.process import process_start


@jd_init
class JdCar:

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-cn",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "car-member.jd.com",
        "Referer": "https://h5.m.jd.com/babelDiy/Zeus/44bjzCpzH9GpspWeBzYSqBA7jEtP/index.html",
    }

    @logger.catch
    async def request(self, session, path, body=None, method='GET'):
        """
        请求数据
        :param method:
        :param path:
        :param body:
        :param session:
        :return:
        """
        try:
            params = {
                'timestamp': str(int(time.time()*1000)),
            }

            url = 'https://car-member.jd.com/api/' + path + '?' + urlencode(params)

            if method == 'GET':
                response = await session.get(url=url)
            else:
                if not body:
                    body = {}
                session.headers.update({'content-type': 'application/json'})
                response = await session.post(url=url, json=body)

            text = await response.text()

            data = json.loads(text)

            return data

        except Exception as e:
            println('{}, 请求服务器错误, {}'.format(self.account, e.args))
            return {
                'status': False
            }

    @logger.catch
    async def exchange_info(self, session):
        """
        兑换
        :return:
        """
        res = await self.request(session, 'v1/user/exchange/bean/check')
        if not res.get('status'):
            println('{}, 兑换失败!'.format(self.account))
            return

        println('{}, 兑换结果:{}'.format(self.account, res['data'].get('reason')))

    @logger.catch
    async def sign(self, session):
        """
        签到
        :return:
        """
        res = await self.request(session, 'v1/user/sign', method='POST')

        if res.get('status'):
            println('{}, 签到成功!'.format(self.account))
        else:
            println('{}, {}'.format(self.account, res.get('error', dict()).get('msg', '未知')))

    @logger.catch
    async def mission(self, session):
        """
        做任务
        :param session:
        :return:
        """
        res = await self.request(session, 'v1/user/mission')
        if not res.get('status'):
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        mission_list = res.get('data', dict()).get('missionList')

        for mission in mission_list:
            if mission['missionType'] not in [1, 5] or mission['missionStatus'] == 2:
                continue

            if mission['missionStatus'] == 0:
                mission_id = mission['missionId']
                res = await self.request(session, 'v1/game/mission', {"missionId": mission_id}, method='POST')
                println('{}, 领取任务:{}, {}'.format(self.account, mission['missionName'], res))
                await asyncio.sleep(2)
                res = await self.request(session, 'v1/user/mission/receive', {"missionId": mission_id}, method='POST')
                println('{}, 完成任务:{}, {}'.format(self.account, mission['missionName'], res))
                await asyncio.sleep(2)

            else:
                res = await self.request(session, 'v1/user/mission/receive', {"missionId": mission['missionId']}, method='POST')
                println('{}, 完成任务:{}, {}'.format(self.account, mission['missionName'], res))
                await asyncio.sleep(2)

    @logger.catch
    async def get_point(self, session):
        """
        领取积分
        :param session:
        :return:
        """
        res = await self.request(session, 'v1/user/point')
        if not res.get('status'):
            return

        remain_point, once_point = res['data']['remainPoint'], res['data']['oncePoint']

        if remain_point > once_point:
            println('{}, 当前积分:{}, 可兑换京豆!'.format(self.account, remain_point))

    async def run(self):
        """
        请求数据
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:
            await self.exchange_info(session)
            await self.sign(session)
            await self.mission(session)
            await self.get_point(session)


if __name__ == '__main__':
    process_start(JdCar, '京东汽车')
