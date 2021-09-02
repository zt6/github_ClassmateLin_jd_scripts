#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/23 9:41 上午
# @File    : jd_shark_bean.py
# @Project : jd_scripts
# @Cron    : 6 0,18,23 * * *
# @Desc    : 京东APP->我的->签到领豆->摇京豆
import asyncio
import time
import aiohttp
import json
from urllib.parse import urlencode

from utils.logger import logger
from utils.console import println
from utils.process import process_start
from utils.jd_init import jd_init

from config import USER_AGENT


@jd_init
class JdSharkBean:
    """
    摇京豆
    """
    headers = {
        'origin': 'https://spa.jd.com',
        'user-agent': USER_AGENT,
        'referer': 'https://spa.jd.com/home?source=JingDou',
        'accept': 'application/json'
    }

    METHOD_GET = 'get'
    METHOD_POST = 'post'

    nickname = None
    sign_info = {}
    bean_count = 0
    red_packet_num = 0
    coupon_list = []

    @logger.catch
    async def request(self, session, params=None, method='get'):
        """
        get 请求
        :param params:
        :param method:
        :param session:
        :return:
        """
        if params is None:
            params = {}

        url = 'https://api.m.jd.com/?{}'.format(urlencode(params))

        try:
            if method == self.METHOD_POST:
                response = await session.post(url)
            else:
                response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            await asyncio.sleep(1)
            return data
        except Exception as e:
            logger.info(e.args)

    @logger.catch
    async def get_index_data(self, session):
        """
        获取首页数据
        :param session:
        :return:
        """
        params = {
            't': int(time.time() * 1000),
            'functionId': 'pg_channel_page_data',
            'appid': 'sharkBean',
            'body': {"paramData": {"token": "dd2fb032-9fa3-493b-8cd0-0d57cd51812d"}}
        }
        println('{}, 获取摇京豆首页数据...'.format(self.account))
        data = await self.request(session, params, self.METHOD_GET)
        return data

    @logger.catch
    async def daily_sign(self, session):
        """
        每日签到
        :param session:
        :return:
        """
        data = await self.get_index_data(session)
        if 'data' not in data or 'floorInfoList' not in data['data']:
            println('{}, 无法获取签到数据:{}'.format(self.account, data))
            return

        sign_info = None

        for floor_info in data['data']['floorInfoList']:
            if 'code' in floor_info and floor_info['code'] == 'SIGN_ACT_INFO':
                cursor = floor_info['floorData']['signActInfo']['currSignCursor']
                token = floor_info['token']
                sign_info = {
                    'status': '',
                    'body': {
                        "floorToken": token,
                        "dataSourceCode": "signIn",
                        "argMap": {
                            "currSignCursor": cursor
                        }
                    }
                }
                for item in floor_info['floorData']['signActInfo']['signActCycles']:
                    if item['signCursor'] == cursor:
                        sign_info['status'] = item['signStatus']

        if not sign_info:
            println('{}, 查找签到数据失败, 无法签到！'.format(self.account))
            return

        if sign_info['status'] != -1:
            println('{}, 当前状态无法签到, 可能已签到过!'.format(self.account))
            return

        # 签到参数
        sign_params = {
            't': int(time.time() * 1000),
            'functionId': 'pg_interact_interface_invoke',
            'appid': 'sharkBean',
            'body': sign_info['body'],
        }

        res = await self.request(session, sign_params, self.METHOD_POST)
        if res.get('success', False):
            println('{}, 签到成功!'.format(self.account))
            for reward in res['data']['rewardVos']:
                if reward['jingBeanVo'] is not None:
                    self.bean_count += int(reward['jingBeanVo']['beanNum'])
                if reward['hongBaoVo'] is not None:
                    self.red_packet_num = float(self.red_packet_num) + float(reward['hongBaoVo'])
        else:
            println('{}, 签到失败!'.format(self.account))

    @logger.catch
    async def do_tasks(self, session):
        """
        做任务
        :param session:
        :return:
        """
        println('{}, 开始做浏览任务！'.format(self.account))
        params = {
            't': int(time.time()),
            'appid': 'vip_h5',
            'functionId': 'vvipclub_lotteryTask',
            'body': {"info": "browseTask", "withItem": 'true'}
        }
        data = await self.request(session, params, self.METHOD_GET)
        if 'data' not in data:
            println('{}, 获取任务列表失败, 无法做任务!'.format(self.account))
            return

        for item in data['data']:
            if 'taskItems' not in item:
                continue
            for task in item['taskItems']:
                if task['finish']:
                    println('{}, 任务: {}, 今日已完成!'.format(self.account, task['title']))
                    continue
                params = {
                    'appid': 'vip_h5',
                    'functionId': 'vvipclub_doTask',
                    'body': {
                        "taskName": "browseTask",
                        "taskItemId": task['id']
                    }
                }
                res = await self.request(session, params, self.METHOD_GET)
                if res.get('success', False):
                    println('{}, 完成{}任务!'.format(self.account, task['title']))
                else:
                    println('{}, 做{}{}任务失败, {}!'.format(self.account, task['title'], task['subTitle'], res))

                await asyncio.sleep(1.5)

        println('{}, 完成浏览任务！'.format(self.account))

    @logger.catch
    async def get_shark_times(self, session):
        """
        获取当前摇奖次数
        :return:
        """
        data = await self.get_index_data(session)
        shark_times = 0
        if 'data' not in data or 'floorInfoList' not in data['data']:
            println('{}, 无法获取摇盒子次数!'.format(self.account))
            return shark_times
        for floor in data['data']['floorInfoList']:
            if 'code' in floor and floor['code'] == 'SHAKING_BOX_INFO':
                shark_times = floor['floorData']['shakingBoxInfo']['remainLotteryTimes']
        return shark_times

    @logger.catch
    async def do_shark(self, session, times=0):
        """
        摇盒子
        :param session:
        :param times:
        :return:
        """
        if times == 0:
            println('{}, 当前无摇盒次数！'.format(self.account))
        else:
            println('{}, 总共可以摇{}次!'.format(self.account, times))
        for i in range(times):
            println('{}, 进行第{}次摇奖!'.format(self.account, i + 1))
            params = {
                'appid': 'sharkBean',
                'functionId': 'vvipclub_shaking_lottery',
                'body': {}
            }
            res = await self.request(session, params, self.METHOD_POST)
            if res.get('success', False):
                if res['data']['lotteryType'] == 2:  # 优惠券
                    coupon_info = res['data']['couponInfo']
                    discount = coupon_info['couponDiscount']
                    quota = coupon_info['couponQuota']
                    limit_str = coupon_info['limitStr']
                    println('{}, 获得满{}减{}优惠券, {}'.format(self.account, quota, discount, limit_str))
                    self.coupon_list.append('获得满{}减{}优惠券, {}'.format(quota, discount, limit_str))

                elif res['data']['lotteryType'] == 5:  # 未中奖
                    println('{}未中奖, 提升京享值可以提高中奖几率和京豆中奖数量!'.format(self.account))

                elif res['data']['lotteryType'] == 0:  # 京豆奖励
                    println('{}, 获得{}京豆'.format(self.account, res['data']['rewardBeanAmount']))
                    self.bean_count += res['data']['rewardBeanAmount']
                else:
                    println('{}, 获得:{}'.format(self.account, res['data']))
                await asyncio.sleep(1)
            else:
                println('{}, 摇盒子失败: {}'.format(self.account, res['resultTips']))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.daily_sign(session)
            await self.do_tasks(session)
            shark_times = await self.get_shark_times(session)
            await self.do_shark(session, shark_times)


if __name__ == '__main__':
    process_start(JdSharkBean, '摇京豆')
