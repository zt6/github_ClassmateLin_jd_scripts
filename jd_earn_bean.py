#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/24 19:43
# @File    : jd_earn_bean.py
# @Project : jd_scripts
# @Cron    : 45 5,22 * * *
# @Desc    : 赚京豆(微信小程序)-赚京豆-签到领京豆
import re
import time
import json
import asyncio
import aiohttp


from urllib.parse import unquote, quote
from utils.console import println
from utils.process import process_start
from utils.logger import logger
from utils.jd_init import jd_init


@jd_init
class JdEarnBean:
    """
    微信小程序 赚京豆
    """
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, '
                      'like Gecko) Mobile/15E217 MicroMessenger/6.8.0(0x16080000) NetType/WIFI Language/en '
                      'Branch/Br_trunk MiniProgramEnv/Mac;',
        "Host": "api.m.jd.com",
        "Referer": "https://servicewechat.com/wxa5bf5ee667d91626/108/page-frame.html",
    }

    async def request(self, session, function_id, body=None, method='GET'):
        """
        :param method:
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        try:
            if body is None:
                body = {}
            url = 'https://api.m.jd.com/api?functionId={}&body={}&appid=swat_miniprogram&client=tjj_m' \
                  '&screen=1920*1080&osVersion=5.0.0&networkType=wifi&sdkName=orderDetail&sdkVersion=1.0.0' \
                  '&clientVersion=3.1.3&area=11&fromType=wxapp&timestamp={}'.format(
                    function_id, quote(json.dumps(body)), int(time.time() * 1000))
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)

            await asyncio.sleep(1)
            text = await response.text()
            data = json.loads(text)
            return data

        except Exception as e:
            println('{}, 请求服务器错误, {}!'.format(self.account, e.args))
            return {
                'success': False
            }

    async def post(self, session, function_id, body=None):
        """
        post请求
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        return await self.request(session, function_id, body, 'POST')

    async def get(self, session, function_id, body=None):
        """
        get请求
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        return await self.request(session, function_id, body, 'GET')
    
    @logger.catch
    async def open_red_packet(self, session, index_data):
        """
        开红包
        :param index_data:
        :param session:
        :return:
        """
        if 'userActivityInfo' not in index_data['floorData']:
            println('{}, 可能是个黑号!'.format(self.account))
            return
        if index_data['floorData']['userActivityInfo']['redPacketOpenFlag']:
            println('{}, 今日已开过红包!'.format(self.account))
            return

        body = {"floorToken": "d7f086c1-5e6e-4572-b8dd-93ec7353d89e", "dataSourceCode": "openRedPacket", "argMap": {}}
        data = await self.post(session, 'pg_interact_interface_invoke', body)
        if not data['success']:
            println('{}, 开红包失败!'.format(self.account))
            return
        println('{}, 开红包成功!')
    
    @logger.catch
    async def do_tasks(self, session):
        """
        :param session:
        :return:
        """
        body = {"channel": "SWAT_RED_PACKET", "systemId": "19", "withAutoAward": 1}
        data = await self.post(session, 'vviptask_receive_list', body)

        if not data['success']:
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        task_list = list(data['data'])

        for task in task_list:
            if task['taskDataStatus'] == 3:
                println('{}, 任务:《{}》已完成过!'.format(self.account, task['name']))
                continue

            if re.search('下单|买|充值|购物|兑换|话费券', task['ruleDesc']) or re.search('下单|买|充值|购物|兑换|话费券', task['subTitle'])\
                    or re.search('下单|买|充值|购物|兑换|话费券', task['name']):
                println('{}, 无法完成该任务:{}, 跳过!'.format(self.account, task['name']))
                continue

            body = {
                "ids": task['id'],
                "systemId": task['systemId'],
                "channel": task['channel']
            }
            res = await self.post(session, 'vviptask_receive_getone', body)
            if not res['success']:
                println('{}, 领取任务:《{}》失败!'.format(self.account, task['name']))
            else:
                println('{}, 领取任务:《{}》成功!'.format(self.account, task['name']))

            body = {
                "taskIdEncrypted": task['id'],
                "systemId": task['systemId'],
                "channel": task['channel']
            }
            res = await self.post(session, 'vviptask_reach_task', body)
            if not res['success']:
                println('{}, 完成任务:《{}》失败!'.format(self.account, task['name']))
            else:
                println('{}, 完成任务:《{}》成功!'.format(self.account, task['name']))

            body = {
                'idEncKey': task['id'],
                "systemId": task['systemId'],
                "channel": task['channel']
            }
            res = await self.post(session, 'vviptask_reward_receive', body)
            if not res['success']:
                println('{}, 领取任务:《{}》奖励失败!'.format(self.account, task['name']))
            else:
                println('{}, 领取任务:《{}》奖励成功!'.format(self.account, task['name']))
    
    @logger.catch
    async def get_index_data(self, session):
        """
        获取首页数据
        :param session:
        :return:
        """
        body = {"paramData": {"token": "3b9f3e0d-7a67-4be3-a05f-9b076cb8ed6a"}}
        data = await self.get(session, 'pg_channel_page_data', body)

        if not data['success']:
            println('{}, 无法获取首页数据!'.format(self.account))
            return None

        data = data['data']

        for item in data['floorInfoList']:
            if item['code'] == 'SWAT_RED_PACKET_ACT_INFO':
                return item

        return None
    
    @logger.catch
    async def receive_bean(self, session):
        """
        领取京豆
        :param session:
        :return:
        """
        body = {"floorToken": "d7f086c1-5e6e-4572-b8dd-93ec7353d89e", "dataSourceCode": "takeReward", "argMap":{}}
        data = await self.post(session, 'pg_interact_interface_invoke', body)

        if not data['success']:
            println('{}, 领取京豆失败, 黑号或者今日已领取奖励!'.format(self.account))
            return

        println('{}, 成功领取京豆, 获得:{}京豆!'.format(self.account, data['data']['rewardBeanAmount']))

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            index_data = await self.get_index_data(session)
            if not index_data:
                println('{}, 无法获取首页数据, 退出程序!'.format(self.account))
                return
            await self.open_red_packet(session, index_data)
            await self.do_tasks(session)
            await self.receive_bean(session)


if __name__ == '__main__':
    process_start(JdEarnBean, '微信小程序-赚京豆')

