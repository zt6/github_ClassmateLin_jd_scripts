#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/28 下午3:59
# @Project : jd_scripts
# @File    : jd_koi_red_packet.py
# @Cron    : 40 0,22 * * *
# @Desc    : 京东APP-签到领豆-边玩边赚-玩锦鲤红包
import asyncio
import json
import time

import aiohttp
from urllib.parse import urlencode

from config import USER_AGENT
from utils.logger import logger
from utils.jd_init import jd_init
from utils.console import println
from utils.process import process_start
from db.model import Code

CODE_KEY = 'jd_koi_red_packet'


@jd_init
class JdKoiRedPacket:
    """
    锦鲤红包
    """

    headers = {
        'user-agent': USER_AGENT,
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://happy.m.jd.com/babelDiy/zjyw/3ugedFa7yA6NhxLN5gw2L3PF9sQC/index.html'
    }

    @logger.catch
    async def request(self, session, function_id='', body=None, method='GET'):
        """
        请求数据
        :param function_id:
        :param session:
        :param body:
        :param method:
        :return:
        """
        try:
            if not body:
                body = {}

            body['isjdapp'] = 1
            if "clientInfo" not in body:
                body["clientInfo"] = {}
            params = {
                'appid': 'jinlihongbao',
                'functionId': function_id,
                'loginType': 2,
                'client': 'jinlihongbao',
                'clientVersion': '10.0.2',
                'osVersion': 'iOS',
                't': int(time.time() * 1000),
                'd_brand': 'iPhone',
                'd_model': 'iPhone',
                'body': json.dumps(body)
            }
            url = 'https://api.m.jd.com/api?' + urlencode(params)
            if method == 'GET':
                response = await session.get(url)
            else:
                response = await session.post(url)

            text = await response.text()

            data = json.loads(text)

            if data['code'] != 0:
                data['biz_code'] = data['code']
                data['biz_msg'] = 'fail'
                return data
            else:
                if 'data' in data:
                    return data['data']
                else:
                    data['biz_code'] = data.get('rtn_code', 999)
                    data['biz_msg'] = data.get('msg', '无法获取数据')
                    return data

        except Exception as e:
            println('{}, 请求服务器数据失败, {}'.format(self.account, e.args))
            return {
                'biz_code': 999,
                'biz_msg': '请求服务器数据错误',
            }

    @logger.catch
    async def browse_receive_coupon_task(self, session):
        """
        做逛领券任务
        :param session:
        :return:
        """
        try:
            url = 'https://api.m.jd.com/client.action?functionId=reportCcTask&clientVersion=10.1.2&build=89743&client=android&d_brand=realme&d_model=RMX2121&osVersion=11&screen=2293*1080&partner=oppo&oaid=&openudid=a27b83d3d1dba1cc&eid=eidAeafa8122b3s2ER7fOlufQwK7mVFsj04l5REe4LVWeGbGBv+dPdm9cyfapfWXwMx9D0ZaJjz97tNXw1NNcphWo1AhMNpCMMsoVHn99RyOtdyF/sZW&sdkVersion=30&lang=zh_CN&uuid=a27b83d3d1dba1cc&aid=a27b83d3d1dba1cc&area=19_1601_36953_50397&networkType=wifi&wifiBssid=unknown&uts=0f31TVRjBSu27%2B9mkBTAWQXEgXkEDpkDa51diXvfKRpvP%2FHgpqt%2FxCcTwfh0OTYPa2yRqcnFJd7uo943KSS5gqsLyUKWzQ%2BmAVH8uGT1FWUyQPuK4kDmqkJDO7ZwDEux9gYTZS%2FvkMnlFEIYfC6jtrMu091uax1cby2nmb0GqJPtmwHL8LayuJlj8gNFgoMPLlNIbx9Xzni4Ujfs%2B1m9Pg%3D%3D&uemps=0-0&harmonyOs=0&st=1630139702138&sign=1595c19442c9f9a898bab223fe535deb&sv=102'
            body = 'body=%7B%22monitorRefer%22%3A%22%22%2C%22monitorSource%22%3A%22ccgroup_android_index_task%22%2C%22taskId%22%3A%22882%22%2C%22taskType%22%3A%221%22%7D&'
            response = await session.post(url, data=body)
            text = await response.text()
            data = json.loads(text)
            if data['code'] == '0':
                println('{}, 完成任务:《逛领券》!'.format(self.account))
        except Exception as e:
            println('{}, 无法完成《逛领券任务》!'.format(self.account, e.args))

    @logger.catch
    async def do_tasks(self, session):
        """
        :return:
        """
        res = await self.request(session, 'taskHomePage')
        if res.get('biz_code') != 0:
            println('{}, 获取任务列表失败!'.format(self.account))
            return None

        task_list = res['result']['taskInfos']

        for task in task_list:

            if task['innerStatus'] == 7:
                res = await self.request(session, 'startTask', {
                    'token': '',
                    'taskType': task['taskType']
                })
                if res.get('biz_code') == 0:
                    println('{}, 成功领取任务:《{}》!'.format(self.account, task['title']))
                    await asyncio.sleep(1)

            if task.get('alreadyReceivedCount', 0) >= task.get('requireCount', 3):
                println('{}, 今日已完成任务:《{}》!'.format(self.account, task['title']))
                continue

            if task['taskType'] == 1:
                await self.browse_receive_coupon_task(session)
                continue

            res = await self.request(session, 'getTaskDetailForColor', {'taskType': task['taskType']})
            if res.get('biz_code') != 0:
                continue
            item_list = res['result']['advertDetails']
            for item in item_list:
                res = await self.request(session, 'taskReportForColor', {
                    'token': '',
                    'taskType': task['taskType'],
                    'detailId': item['id']
                })
                if res.get('biz_code') == 0:
                    println('{}, 完成任务:《{}》'.format(self.account, item['name']))
                await asyncio.sleep(1)

            await asyncio.sleep(1)

    @logger.catch
    async def run_help(self):
        """
        助力入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            item_list = Code.get_code_list(code_key=CODE_KEY)

            for item in item_list:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue
                res = await self.request(session, 'jinli_h5assist',
                                         {"clientInfo": {}, "redPacketId": code, "followShop": 0})
                if res.get('biz_code') != 0:
                    println('{}, 助力好友失败:{}!'.format(self.account, account))
                    break

                println('{}, 助力好友:{}, {}'.format(self.account, account, res['result']['statusDesc']))

                if res['result']['status'] == 3:  # 今日助力次数已满
                    break

    @logger.catch
    async def open_red_packet(self, session):
        """
        开红包
        :param session:
        :return:
        """
        res = await self.request(session, 'taskHomePage')
        if res.get('biz_code') != 0:
            println('{}, 获取任务列表失败!'.format(self.account))
            return None

        task_list = res['result']['taskInfos']

        for task in task_list:
            if task['innerStatus'] != 3:
                continue
            res = await self.request(session, 'h5receiveRedpacketAll', {"clientInfo": {}, "taskType": task['taskType']})
            if res.get('biz_code') == 0:
                println('{}, 开红包成功, 获得:{}元!'.format(self.account, res['result']['discount']))

            await asyncio.sleep(1)

        for i in range(8):
            res = await self.request(session, 'h5receiveRedpacketAll')
            if res.get('biz_code') == 0:
                println('{}, 开红包成功, 获得:{}元!'.format(self.account, res['result']['discount']))
            else:
                println('{}, 开红包失败, {}'.format(self.account, res['biz_msg']))
                break

    @logger.catch
    async def get_share_code(self, session):
        """
        获取助力码
        :param session:
        :return:
        """
        res = await self.request(session, 'h5activityIndex')
        data = res.get('result', None)
        if not data:
            return False

        code = data['redpacketInfo'].get('id', None)
        if not code:
            res = await self.request(session, 'h5launch', {"clientInfo": {}, "followShop": 0})
            if res.get('biz_code') == 0:
                code = res['result']['redPacketId']

        if not code:
            println('{}, 获取助力码失败!'.format(self.account))
        else:
            Code.insert_code(code_key=CODE_KEY, code_val=code, account=self.account, sort=self.sort)
            println('{}, 助力码:{}'.format(self.account, code))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.do_tasks(session)
            await self.open_red_packet(session)
            await self.get_share_code(session)


if __name__ == '__main__':
    process_start(JdKoiRedPacket, '锦鲤红包', code_key=CODE_KEY)
