#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/31 下午6:25
# @Project : jd_scripts
# @File    : jd_flash_sale_box.py
# @Cron    : 15 5,23 * * *
# @Desc    : 京东APP->品牌闪购->闪购盲盒
import asyncio
import aiohttp
import json
from urllib.parse import urlencode
from utils.console import println
from utils.process import process_start
from utils.logger import logger
from utils.jd_init import jd_init
from db.model import Code
from config import USER_AGENT

# 闪购盲盒助力码
CODE_FLASH_SALE_BOX = 'flash_sale_box'


@jd_init
class JdFlashSaleBox:
    """
    闪购盲盒
    """
    headers = {
        'user-agent': USER_AGENT,
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://h5.m.jd.com',
        'referer': 'https://h5.m.jd.com/',

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
            url = 'https://api.m.jd.com/client.action?'
            params = {
                'functionId': function_id,
                'body': json.dumps(body),
                'client': 'wh5',
                'clientVersion': '1.0.0'
            }
            url += urlencode(params)

            if method == 'GET':
                response = await session.get(url)
            else:
                response = await session.post(url)

            text = await response.text()
            data = json.loads(text)
            return data

        except Exception as e:
            println('{}, 获取服务器数据失败:{}!'.format(self.account, e.args))
            return {
                'code': 9999
            }

    async def receive_or_finish_task(self, session, task, action_type=1):
        """
        领取任务或完成任务
        :return:
        """
        pass
    
    @logger.catch
    async def do_task(self, session, task):
        """
        做任务
        :param session:
        :param task:
        :return:
        """
        do_times = task['times']  # 已经完成的次数
        max_times = task['maxTimes']
        task_name = task['taskName']
        task_id = task['taskId']
        if do_times >= max_times:
            println('{}, 任务《{}》已完成!'.format(self.account, task_name))
            return

        if 'waitDuration' in task and task['waitDuration'] > 0:
            timeout = task['waitDuration']
        else:
            timeout = 2

        if 'productInfoVos' in task:
            item_list = task['productInfoVos']
        elif 'browseShopVo' in task:
            item_list = task['browseShopVo']
        elif 'shoppingActivityVos' in task:
            item_list = task['shoppingActivityVos']
        else:
            item_list = []

        for item in item_list:
            if do_times > max_times:
                break
            body = {
                "appId": "1EFRXxg",
                "taskToken": item['taskToken'],
                "taskId": task_id,
                "actionType": 1
            }
            res = await self.request(session, 'harmony_collectScore', body)
            if res['code'] == 0:
                println('{}, 任务:《{}》,{}!'.format(self.account, task_name, res['data']['bizMsg']))
            else:
                println('{}, 任务:{}领取失败!'.format(self.account, task_name))

            println('{}, 正在做任务:{}, 等待{}秒!'.format(self.account, task_name, timeout))
            await asyncio.sleep(timeout)

            body = {
                "appId": "1EFRXxg",
                "taskToken": item['taskToken'],
                "taskId": task_id,
                "actionType": 0
            }
            res = await self.request(session, 'harmony_collectScore', body)
            if res['code'] != 0:
                continue
            println('{}, {}!'.format(self.account, res['data']['bizMsg']))
            do_times += 1
    
    @logger.catch
    async def do_tasks(self, session):
        """
        :param session:
        :return:
        """
        res = await self.request(session, 'healthyDay_getHomeData', {"appId":"1EFRXxg","taskToken":"","channelId":1})
        if res['code'] != 0 or res['data']['bizCode'] != 0:
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        data = res['data']['result']
        task_list = data['taskVos']

        for task in task_list:
            task_name, task_type = task['taskName'], task['taskType']
            if task_type == 14:   # 邀请好友助力
                code = task['assistTaskDetailVo']['taskToken']
                println('{}, 助力码:{}'.format(self.account, code))
                Code.insert_code(code_key=CODE_FLASH_SALE_BOX, code_val=code, account=self.account, sort=self.sort)
                continue
            await self.do_task(session, task)

    @logger.catch
    async def run_help(self):
        """
        助力
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            item_list = Code.get_code_list(code_key=CODE_FLASH_SALE_BOX)
            for item in item_list:
                friend_account, friend_code = item['account'], item['code']
                if friend_account == self.account:
                    return
                body = {
                    "appId": "1EFRXxg",
                    "taskToken": friend_code,
                    "taskId": 6,
                    "actionType": 0
                }
                res = await self.request(session, 'harmony_collectScore', body)
                if res['code'] != 0:
                    println('{}, 助力好友:{}失败!'.format(self.account, friend_account))
                    break

                if res['data']['bizCode'] != 0:
                    println('{}, 助力好友:{}失败, {}!'.format(self.account, friend_account, res['data']['bizMsg']))
                    if res['data']['bizCode'] in [108]:
                        break
                else:
                    println('{}, 助力好友:{}成功!'.format(self.account, friend_account))

                await asyncio.sleep(1)

    @logger.catch
    async def lottery(self, session):
        """
        抽奖
        :param session:
        :return:
        """
        println('{}, 正在查询抽奖次数!'.format(self.account))
        res = await self.request(session, 'healthyDay_getHomeData',
                                 {"appId": "1EFRXxg", "taskToken": "", "channelId": 1})
        if res['code'] != 0 or res['data']['bizCode'] != 0:
            println('{}, 查询抽奖次数失败!'.format(self.account))
            return

        times = int(res['data']['result']['userInfo']['lotteryNum'])

        if times < 1:
            println('{}, 当前已无抽奖次数!'.format(self.account))
            return

        println('{}, 当前有{}次抽奖机会, 开始抽奖!'.format(self.account, times))

        for i in range(1, times+1):
            await asyncio.sleep(1)
            res = await self.request(session, 'interact_template_getLotteryResult', {"appId": "1EFRXxg"})
            if res['code'] != 0 or res['data']['bizCode'] != 0:
                println('{}, 第{}次抽奖失败, 退出抽奖'.format(self.account, i))
                break
            if res['data']['result']['userAwardsCacheDto']['type'] == 0:
                println('{}, 第{}次抽奖, 未抽中奖励!'.format(self.account, i))
            elif res['data']['result']['userAwardsCacheDto']['type'] == 2:
                println('{}, 第{}次抽奖, 获得{}'.format( self.account, i,
                        res['data']['result']['userAwardsCacheDto']['jBeanAwardVo']['prizeName']))
            else:
                println('{}, 第{}次抽奖, 获得奖励未知~'.format(self.account, i))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            await self.do_tasks(session)
            await self.lottery(session)


if __name__ == '__main__':
    process_start(JdFlashSaleBox, '京东APP-闪购盲盒', code_key=CODE_FLASH_SALE_BOX)
