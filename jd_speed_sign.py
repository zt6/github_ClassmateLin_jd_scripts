#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @File         : jd_speed_sign.py
# @Project      : jd_scripts
# @Time         : 2021-09-20 01:41:44
# @Last Modified: 2021-09-21 11:23:35
# @Cron         : 10 7 * * *
# @Desc         : 京东极速版app 签到和金币任务

import asyncio
import time
import json
import hmac
import aiohttp
from urllib.parse import quote, urlencode

from utils.jd_init import jd_init
from utils.console import println
from utils.process import process_start
from utils.logger import logger


@jd_init
class JdSpeedSign:
    """京东极速版
    """

    headers = {
        'Host': 'api.m.jd.com',
        'Accept': '*/*',
        'Connection': 'keep-alive',
        'user-agent': 'jdltapp;iPad;3.1.0;14.4;network/wifi;Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148;supportJDSHWK/1")',
        'Accept-Language': 'zh-Hans-CN;q=1,en-CN;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': "application/x-www-form-urlencoded",
        "referer": "https://an.jd.com/babelDiy/Zeus/q1eB6WUB8oC4eH1BsCLWvQakVsX/index.html"
    }

    score = 0 # 本次获得金币
    total = 0 # 总金币
    host = 'https://api.m.jd.com/'

    async def request_sign(self, session, functionId, body=None, method='GET'):
        """请求

        Args:
            session ([type]): [description]
            functionId ([type]): [description]
            body ([type], optional): [description]. Defaults to None.
            method (str, optional): [description]. Defaults to 'GET'.
        """
        headers = {
            'Host': 'api.m.jd.com',
            'accept': '*/*',
            'kernelplatform': 'RN',
            'user-agent': 'JDMobileLite/3.1.0 (iPad; iOS 14.4; Scale/2.00)',
            'accept-language': 'zh-Hans-CN;q=1, ja-CN;q=0.9'
        }
        timestamp = int(time.time() * 1000)
        if not body:
            body = {}
        body_str = json.dumps(body)
        content = f'lite-android&{body_str}&android&3.1.0&{functionId}&{timestamp}&846c4c32dae910ef'
        key = '12aea658f76e453faf803d15c40a72e0'
        sign = hmac.new(key.encode('utf-8'), content.encode('utf-8'), 'SHA256').hexdigest()
        url = f'https://api.m.jd.com/api?functionId={functionId}&body={quote(body_str)}&appid=lite-android&client=android&uuid=846c4c32dae910ef&clientVersion=3.1.0&t={timestamp}&sign={sign}'
        
        try:
            response = await session.get(url, headers=headers)
            text = await response.text()
            data = json.loads(text)
            return data
        except Exception as e:
            println('{}, 请求服务器数据失败,{}!'.format(self.account, e.args))

    async def request(self, session, functionId, body=None, method='GET'):
        """无sign请求

        Args:
            session ([type]): [description]
            functionId ([type]): [description]
            body ([type], optional): [description]. Defaults to None.
            method (str, optional): [description]. Defaults to 'GET'.
        """
        timestamp = int(time.time() * 1000)
        default_params = {
            'functionId': functionId,
            'appid': 'activities_platform',
            '_t': timestamp
        }
        if not body:
            body = {}
        default_params['body'] = json.dumps(body)
        try:
            if method == 'GET':
                url = self.host + '?' + urlencode(default_params)
                response = await session.get(url, headers=self.headers)
            elif method == 'POST':
                url = self.host
                response = await session.post(url, data=urlencode(default_params), headers=self.headers)
            text = await response.text()
            data = json.loads(text)
            if data['code'] == 0:
                return data['data']
            else:
                println('{}, 请求服务器数据失败({})!'.format(self.account, data))
                return data
        except Exception as e:
            println('{}, 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))
            return {

            }

    async def rich_man_index(self, session):
        """红包大富翁

        Args:
            session (ClientSession): [description]
        """
        body = {
            "actId": "hbdfw",
            "needGoldToast": "true"
        }
        data = await self.request_sign(session, 'richManIndex', body)
        try:
            if data['code'] == 0 and data['data']:
                println('{}, {}'.format(self.account, data['data']))
                randomTimes = data['data']['userInfo']['randomTimes']
                while randomTimes > 0:
                    await self.shoot_rich_man_dice(session)
                    randomTimes -= 1
            else:
                println('{}, {}'.format(self.account, data.get('msg')))
        except Exception as e:
            println('{}, 红包大富翁 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))

    async def shoot_rich_man_dice(self, session):
        """红包大富翁
        """
        body = {
            "actId": "hbdfw"
        }
        data = await self.request_sign(session, 'shootRichManDice', body)
        try:
            if data['code'] == 0 and not data.get('data') and not data['data'].get('rewardType') and not data['data'].get('couponDesc'):
                println('{}, 红包大富翁抽奖获得：【{}-{} {}】'.format(self.account, data['data']['couponUsedValue'], data['data']['rewardValue'], data['data']['poolName']))
            else:
                println('{}, 红包大富翁抽奖：获得空气'.format(self.account))
        except Exception as e:
            println('{}, 红包大富翁抽奖 请求服务器数据失败,{}!'.format(self.account, e.args))


    async def wheels_home(self, session):
        """大转盘
        """
        body = {
            "linkId": "toxw9c5sy9xllGBr3QFdYg"
        }
        data = await self.request(session, 'wheelsHome', body)
        try:
            if data['lotteryChances'] > 0:
                times = data['lotteryChances']
                while times > 0:
                    await self.wheels_lottery(session)
                    times -= 1
                    await asyncio.sleep(0.5)
            else:
                println('{}, 大转盘 已无次数!'.format(self.account))
        except Exception as e:
            println('{}, 大转盘 请求服务器数据失败,{}!'.format(self.account, e.args))

    async def wheels_lottery(self, session):
        """大转盘抽奖
        """
        body = {
            "linkId": "toxw9c5sy9xllGBr3QFdYg"
        }
        data = await self.request(session, 'wheelsLottery', body)
        try:
            if data['rewardType']:
                # prizeCode
                desc = data.get('couponDesc')
                if not desc:
                    desc = data.get('prizeCode')
                println('{}, 幸运大转盘抽奖获得:【{}-{} {}】'.format(self.account, data.get('couponUsedValue'), data.get('rewardValue'), desc))
        except Exception as e:
            println('{}, 大转盘抽奖 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))
    
    @logger.catch
    async def ap_task_list(self, session):
        """获取大转盘任务
        """
        body = {
            "linkId": "toxw9c5sy9xllGBr3QFdYg"
        }
        println('{}, 开始做大转盘任务.'.format(self.account))
        data = await self.request(session, 'apTaskList', body)
        try:
            for task in data:
                if task['taskFinished'] == False and task['taskType'] in ['SIGN','BROWSE_CHANNEL']:
                    println('{}, 去做任务: {}'.format(self.account, task['taskTitle']))
                    await self.ap_do_task(session, task['taskType'], task['id'], 4, task['taskSourceUrl'])
                else:
                    println('{}, 任务 {} 已做过, 跳过.'.format(self.account, task['taskTitle']))
        except Exception as e:
            println('{}, 大转盘任务 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def ap_do_task(self, session, taskType, taskId, channel, itemId):
        """大转盘做任务
        """
        body = {
            "linkId": "toxw9c5sy9xllGBr3QFdYg",
            "taskType": taskType,
            "taskId": taskId,
            "channel": channel,
            "itemId": itemId
        }
        data = await self.request(session, 'apDoTask', body)
        try:
            if data['finished']:
                println('{}, 任务完成!'.format(self.account))
        except Exception as e:
            println('{}, 大转盘做任务失败,{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def sign_init(self, session):
        """签到 init
        """
        body = {
            "activityId": "8a8fabf3cccb417f8e691b6774938bc2",
            "kernelPlatform": "RN",
            "inviterId":"U44jAghdpW58FKgfqPdotA=="
        }
        data = await self.request_sign(session, 'speedSignInit', body)
        try:
            println('{}, sign_init {}'.format(self.account, data))
        except Exception as e:
            println('{}, 签到 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def sign(self, session):
        """签到
        """
        body = {
            "kernelPlatform": "RN",
            "activityId": "8a8fabf3cccb417f8e691b6774938bc2",
            "noWaitPrize": "false"
        }
        data = await self.request_sign(session, 'speedSign', body)
        try:
            if data['subCode'] == 0:
                println('{}, 签到得到{}现金,共计获得{}'.format(self.account, data['data']['signAmount'], data['data']['cashDrawAmount']))
            else:
                println('{}, 签到失败!({})'.format(self.account, data))
        except Exception as e:
            println('{}, 签到 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def task_list(self, session):
        """金币任务列表
        """
        body = {
            "version": "3.1.0",
            "method": "newTaskCenterPage",
            "data": {
                "channel": 1
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            for task in data['data']:
                self.task_name = task['taskInfo']['mainTitle']
                if task['taskInfo']['status'] == 0:
                    if task['taskType'] >= 1000:
                        await self.do_task(session, task['taskType'])
                        await asyncio.sleep(1)
                    else:
                        self.canStartNewItem = True
                        while self.canStartNewItem:
                            if task['taskType'] != 3:
                                await self.query_item(session, task['taskType'])
                            else:
                                await self.start_item(session, "", task['taskType'])
                else:
                    println('{}, {} 已做过, 跳过.'.format(self.account, self.task_name))
        except Exception as e:
            println('{}, 大转盘任务 请求服务器数据失败,{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def do_task(self, session, taskId):
        """做金币任务
        """
        body = {
            "method": "marketTaskRewardPayment",
            "data": {
                "channel": 1, 
                "clientTime": int(time.time() * 1000) + 0.588,
                "activeType": taskId
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['code'] == 0:
                println('{}, {} 任务已完成,预计获得{}金币'.format(self.account, data['data']['taskInfo']['mainTitle'], data['data']['reward']))
        except Exception as e:
            println('{}, 做任务失败,{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def query_item(self, session, activeType):
        """查询商品任务
        """
        body = {
            "method": "queryNextTask",
            "data": {
                "channel": 1,
                "activeType": activeType
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['code'] == 0:
                await self.start_item(session, data['data']['nextResource'], activeType)
            else:
                println('{}, 商品任务开启失败,{}!'.format(self.account, data['message']))
                self.canStartNewItem = False
        except Exception as e:
            println('{}, 商品任务开启失败.{}({})!'.format(self.account, e.args, data))
            self.canStartNewItem = False

    @logger.catch
    async def start_item(self, session, activeId, activeType):
        """开启商品任务
        """
        body = {
            "method": "enterAndLeave",
            "data": {
                "activeId": activeId,
                "clientTime": int(time.time() * 1000),
                "channel": "1",
                "messageType": "1",
                "activeType": activeType,
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['code'] == 0:
                if data['data']['taskInfo']['isTaskLimit'] == 0:
                    videoBrowsing = data['data']['taskInfo'].get('videoBrowsing')
                    taskCompletionProgress = data['data']['taskInfo']['taskCompletionProgress']
                    taskCompletionLimit = data['data']['taskInfo']['taskCompletionLimit']
                    if activeType != 3:
                        videoBrowsing = 5 if activeType == 1 else 10
                    println(f'{self.account},【{taskCompletionProgress + 1}/{taskCompletionLimit}】浏览商品任务记录成功，等待{videoBrowsing}秒')
                    await asyncio.sleep(videoBrowsing)
                    await self.end_item(session,data['data']['uuid'], activeType, activeId, videoBrowsing if activeType == 3 else "")
                else:
                    println('{}, {}任务已达上限!'.format(self.account, self.task_name))
                    self.canStartNewItem = False
            else:
                println('{}, 商品任务开启失败,{}!'.format(self.account, data['message']))
                self.canStartNewItem = False
        except Exception as e:
            println('{}, 商品任务开启失败.{}({})!'.format(self.account, e.args, data))
            self.canStartNewItem = False

    @logger.catch
    async def end_item(self, session, uuid, activeType, activeId = "", videoTimeLength = ""):
        """结束商品任务
        """
        body = {
            "method": "enterAndLeave",
            "data": {
                "channel": "1",
                "clientTime": int(time.time() * 1000),
                "uuid": uuid,
                "videoTimeLength": videoTimeLength,
                "messageType": "2",
                "activeType": activeType,
                "activeId": activeId
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['code'] == 0 and data['isSuccess']:
                await self.reward_item(session,uuid, activeType, activeId, videoTimeLength)
            else:
                println('{}, {}任务结束失败{}!'.format(self.account, self.task_name, data['message']))
        except Exception as e:
            println('{}, 任务结束失败{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def reward_item(self, session, uuid, activeType, activeId = "", videoTimeLength = ""):
        """领取商品任务奖励金币
        """
        body = {
            "method": "rewardPayment",
            "data": {
                "channel": "1",
                "clientTime": int(time.time() * 1000),
                "uuid": uuid,
                "videoTimeLength": videoTimeLength,
                "messageType": "2",
                "activeType": activeType,
                "activeId": activeId
            }
      }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['code'] == 0 and data['isSuccess']:
                self.score += data['data']['reward']
                println('{}, {}任务完成,获得{}金币!'.format(self.account, self.task_name, data['data']['reward']))
            else:
                println('{}, {}任务失败{}!'.format(self.account, self.task_name, data['message']))
        except Exception as e:
            println('{}, 任务失败{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def query_joy(self, session):
        """查询气泡
        """
        body = {
            "method": "queryJoyPage",
             "data": {
                "channel": 1
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['data']['taskBubbles']:
                for task in data['data']['taskBubbles']:
                    await self.reward_task(session, task['id'], task['activeType'])
                    await asyncio.sleep(0.5)
        except Exception as e:
            println('{}, 收气泡失败{}!'.format(self.account, e.args))

    @logger.catch
    async def reward_task(self, session, id, taskId):
        """领取气泡奖励
        """
        body = {
            "method": "joyTaskReward",
            "data": {
                "id": id,
                "channel": 1, 
                "clientTime": int(time.time() * 1000) + 0.588, 
                "activeType": taskId
            }
        }
        data = await self.request_sign(session, 'ClientHandleService.execute', body)
        try:
            if data['code'] == 0:
                self.score += data['data']['reward']
                println('{}, 气泡收取成功，获得{}金币!'.format(self.account, data['data']['reward']))
            else:
                println('{}, 气泡收取失败，{}!'.format(self.account, data['message']))
        except Exception as e:
            println('{}, 气泡收取失败，{}({})!'.format(self.account, e.args, data))

    @logger.catch
    async def cash(self, session):
        """获取当前金币
        """
        body = {
            "method": "userCashRecord", 
            "data": {
                "channel": 1, 
                "pageNum": 1, 
                "pageSize": 20
            }
        }
        data = await self.request_sign(session, 'MyAssetsService.execute', body)
        try:
            if data['code'] == 0:
                self.total = data['data']['goldBalance']
        except Exception as e:
            println('{}, 获取cash信息失败，{}({})!'.format(self.account, e.args, data))

    async def show_msg(self):
        """show msg
        """
        self.message = f'【京东账号】{self.account}\n'
        gold_tips = f'【运行结果】本次运行获得{self.score}金币，共计{self.total}金币'
        self.message += f'{gold_tips}\n'
        println('{}, {}'.format(self.account, gold_tips))
        self.message += f'【红包】可兑换 {self.total/10000:.2f} 元京东红包\n'
        self.message += f'【兑换入口】京东极速版->我的->金币\n'

    async def run(self):
        """run
        """
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            # 暂时过期
            # await self.rich_man_index(session)

            await self.wheels_home(session)
            await self.ap_task_list(session)
            await self.wheels_home(session)

            # await self.sign_init(session)
            # await self.sign(session)

            await self.task_list(session)
            await self.query_joy(session)
            # await self.sign_init(session)
            await self.cash(session)
            await self.show_msg()

        
if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = JdSpeedSign(**JD_COOKIES[0])
    # asyncio.run(app.run())

    process_start(JdSpeedSign, '京东极速版签到')