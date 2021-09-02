#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/28 4:37 下午
# @File    : dj_bean_manor.py
# @Project : jd_scripts
# @Cron    : 30 6,21 * * *
# @Desc    : 京东APP->京东到家->签到->鲜豆庄园
import asyncio
import time

import aiohttp
import random

from utils.console import println
from utils.dj_init import dj_init
from utils.logger import logger
from db.model import Code
from utils.process import get_code_list

# 鲜豆庄园助力码
CODE_DJ_BEAN_MANOR = 'dj_bean_manor'


@dj_init
class DjBeanManor:
    """
    京东到家->鲜豆庄园
    """
    activity_id = None
    water_num = 0  # 当前水滴
    level = 0  # 当前等级

    @logger.catch
    async def get_activity_info(self, session):
        """
        获取活动数据
        :param session:
        :return:
        """
        res = await self.post(session, 'plantBeans/getActivityInfo')
        if res['code'] != '0':
            return None
        activity_info = res['result']['cur']
        self.activity_id = activity_info['activityId']
        self.water_num = activity_info['water']
        self.level = activity_info['level']
        return activity_info

    @logger.catch
    async def initiate_help(self, session):
        """
        发起助力红包
        :param session:
        :return:
        """
        res = await self.get(session, 'xapp/friendHelp/list')
        if res['code'] != '0':
            println('{}, 无法获取助力信息!')
            return
        item_list = res['result']['friendHelpVOList']
        if len(item_list) < 1:
            println('{}, 助力红包列表为空, 无法发起!'.format(self.account))
            return
        item = random.choice(item_list)

        res = await self.get(session, 'xapp/friendHelp/join', {"activityId": item['activityId']})
        if res['code'] == '0':
            println('{}, 成功发起助力红包!'.format(self.account))
        else:
            println('{}, 无法发起助力红包!'.format(self.account))

    @logger.catch
    async def collect_watter(self, session):
        """
        收水滴
        :param session:
        :return:
        """
        res = await self.post(session, 'plantBeans/getWater', {"activityId": self.activity_id})
        if res['code'] == '0':
            println('{}, 成功收取水滴!'.format(self.account))
        else:
            println('{}, 收取水滴失败!'.format(self.account))

    @logger.catch
    async def watering(self, session, num=200, times=10):
        """
        :param times: 浇水多少次
        :param num: 每次浇水克数
        :param session:
        :return:
        """
        # 刷新当前水滴数量
        await self.get_activity_info(session)
        await asyncio.sleep(1)

        if num * times > self.water_num:
            water_num = self.water_num
        else:
            water_num = times * num

        if water_num < 100:
            println('{}, 水滴不足, 不浇水!'.format(self.account))
            return

        res = await self.post(session, 'plantBeans/watering', {"activityId": self.activity_id,
                                                                  "waterAmount": water_num})
        if res['code'] == '0':
            println('{}, 成功浇水{}g!'.format(self.account, water_num))
        else:
            println('{}, 浇水失败, {}!'.format(self.account, res['msg']))

    async def click_tree(self, session):
        """
        点树苗
        :return:
        """
        for i in range(15):
            res = await self.post(session, 'plantBeans/beansLottery', {"activityId": self.activity_id})
            if res.get('code') == '0':
                result = res['result']
                if 'text' in result:
                    text = result['text']
                elif 'title' in result:
                    text = result['title']
                else:
                    text = '结果未知'
                println('{}, 点击树苗, {}'.format(self.account, text))
            else:
                break
            await asyncio.sleep(1)

    @logger.catch
    async def do_task(self, session):
        """
        做任务
        :param session:
        :return:
        """
        res = await self.get(session, 'task/list', {"modelId": "M10003", "plateCode": 3})
        if res['code'] != '0':
            println('{}, 无法获取任务列表!'.format(self.account))
            return

        task_list = res['result']['taskInfoList']

        for task in task_list:
            task_type, task_name = task['taskType'], task['taskName']

            if task['status'] == 3:  # 任务完成并且领取了水滴
                println('{}, 任务:《{}》今日已完成!'.format(self.account, task_name))
                continue

            if task['status'] == 2:  # 任务完成，但未领水滴
                await self.get_task_award(session, task)
                continue

            if task_type in [307, 310, 901, 603, 601, 503]:  # 浏览类型任务
                await self.browse_task(session, task)
                await self.get_task_award(session, task)
            elif task_type == 401:  # 发起助力红包
                await self.receive_task(session, task)
                await self.initiate_help(session)
                await self.get_task_award(session, task)
            else:
                await self.receive_task(session, task)

    @logger.catch
    async def get_share_code(self, session):
        """
        获取助力码
        :return:
        """
        res = await self.get(session, 'signin/carveUp/carveUpInfo', {"groupId": "", "type": 2})
        if res.get('code') != '0':
            println('{}, 获取组队数据失败!'.format(self.account))
            return
        if 'groupId' not in res['result']:
            println('{}, 开启队伍!'.format(self.account))
            res = await self.get(session, 'signin/carveUp/openCarveUp', {"nickName": "",
                                                                         "nickHeadUrl": "",
                                                                         "wcUnionId": "",
                                                                         "openId": "",
                                                                         "formId": "",
                                                                         "type": 2,
                                                                         "traceId": int(time.time()*1000)})
        code = res['result']['groupId']
        println('{}, 助力码:{}'.format(self.account, code))
        Code.insert_code(code_key=CODE_DJ_BEAN_MANOR, code_val=code, account=self.account, sort=self.sort)

    @logger.catch
    async def run_help(self):
        """
        组队
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            dj_cookies = await self.login(session)
            if not dj_cookies:
                return
            println('{}, 登录成功...'.format(self.account))

        async with aiohttp.ClientSession(cookies=dj_cookies, headers=self.headers) as session:
            activity_info = await self.get_activity_info(session)
            if not activity_info:
                println('{}, 获取活动ID失败, 退出程序!'.format(self.account))
                return
            item_list = Code.get_code_list(CODE_DJ_BEAN_MANOR)
            item_list.extend(get_code_list(CODE_DJ_BEAN_MANOR))

            for item in item_list:
                account, code = item.get('account'), item.get('code')
                # 参数加密了
                res = await self.get(session, 'signin/carveUp/joinCarveUp', {"groupId": code, "type": 2})
                println(res)
                if res.get('code') != '0':
                    println('{}, 无法加入好友:{}的队伍!'.format(self.account, account))
                else:
                    println(res)
                    println('{}, 加入好友:{}队伍结果, {}'.format(self.account, account, res['result']['title']))
                    if '上限' in res['result']['title']:
                        break

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            dj_cookies = await self.login(session)
            if not dj_cookies:
                return
            println('{}, 登录成功...'.format(self.account))

        async with aiohttp.ClientSession(cookies=dj_cookies, headers=self.headers) as session:
            activity_info = await self.get_activity_info(session)
            if not activity_info:
                println('{}, 获取活动ID失败, 退出程序!'.format(self.account))
                return
            await self.do_task(session)
            await self.click_tree(session)
            # await self.get_share_code(session)


if __name__ == '__main__':
    from utils.process import process_start
    process_start(DjBeanManor, '鲜豆庄园任务')
