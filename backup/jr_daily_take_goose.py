#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/24 11:08 上午
# @File    : jr_daily_take_goose.py
# @Project : jd_scripts
# @Cron    : 35 9,22 * * *
# @Desc    : 京东金融APP->天天提鹅
import asyncio
import json
import aiohttp

from urllib.parse import quote
from utils.console import println
from utils.jd_init import jd_init
from utils.logger import logger
from furl import furl
from config import USER_AGENT


@jd_init
class JrDailyTakeGoose:
    """
    天天提额
    """
    headers = {
        'Accept': 'application/json',
        'Origin': 'https://uua.jr.jd.com',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Host': 'ms.jr.jd.com',
        'Connection': 'keep-alive',
        'User-Agent': USER_AGENT,
        'Referer': 'https://uua.jr.jd.com/uc-fe-wxgrowing/moneytree/index',
        'Accept-Language': 'zh-cn'
    }
    egg_num = 0  # 本次运行总共获得的鹅蛋总数
    integral = 0  # 兑换了多少积分

    async def request(self, session, function_id, body):
        """
        发起请求
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/' + function_id
        body = 'reqData={}'.format(quote(json.dumps(body)))
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            await asyncio.sleep(1)
            return data
        except Exception as e:
            println('{}, 无法获取服务器数据!{}'.format(self.account, e.args))

    @logger.catch
    async def request_mission(self, session, function_id, body):
        """
        URL`https://ms.jr.jd.com/gw/generic/mission/h5/m/xxx`的请求函数
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        url = 'https://ms.jr.jd.com/gw/generic/mission/h5/m/{}?reqData={}'.format(function_id, quote(json.dumps(body)))
        try:
            response = await session.get(url=url)
            text = await response.text()
            data = json.loads(text)
            return data
        except Exception as e:
            println("{}, 访问服务器异常, 信息:{}".format(self.account, e.args))

    @logger.catch
    async def query_task_list(self, session):
        """
        查询任务列表
        :param session:
        :return:
        """
        task_result = []
        body = {
            "riskDeviceInfo": "{}",
            "channelLv": "",
            "environment": "other"
        }
        task_list = []
        data = await self.request(session, 'queryGooseTaskList', body)
        if data['resultCode'] != 0 or data['resultData']['code'] != '0000':
            println('{}, 查询任务列表失败!'.format(self.account))
            return task_list
        task_list = data['resultData']['data']

        for task in task_list:
            if task['status'] == 2:  # 已完成任务跳过
                continue

            if 'doLink' not in task:
                continue

            url = furl(task['doLink'])
            real_time = int(url.args.get('readTime', 0))
            if real_time == 0:  # 非浏览类型任务， 无法完成， 跳过!
                continue
            task['real_time'] = real_time
            task_result.append(task)

        return task_result

    @logger.catch
    async def do_task_list(self, session, task_list):
        """
        做任务
        :param session:
        :param task_list:
        :return:
        """
        if len(task_list) == 0:
            println('{}, 当前无可做任务!'.format(self.account))
            return

        for task in task_list:
            params = {
                "missionId": str(task['missionId']),
                "shareUuid": "",
                "riskDeviceInfo": "{}",
                "channelLv": "",
                "environment": "other"
            }
            res = await self.request(session, 'receiveGooseTask', params)
            if res['resultCode'] != 0 or res['resultData']['code'] != '0000':
                if res['resultCode'] != 0:
                    reason = res['resultMsg']
                else:
                    reason = res['resultData']['msg']
                println('{}, 任务:{}, 领取失败, 原因:{}'.format(self.account, task['name'], reason))

            res = await self.request_mission(session, 'queryMissionReceiveAfterStatus',
                                             {"missionId": str(task['missionId'])})
            if not res or res['resultCode'] != 0 or res['resultData']['code'] != '0000':
                if res['resultCode'] != 0:
                    reason = res['resultMsg']
                else:
                    reason = res['resultData']['msg']
                println('{}, 任务:{}, 初始化失败!原因:{}'.format(self.account, task['name'],  reason))
                continue

            println('{}, 正在进行任务:{}, 等待{}s!'.format(self.account, task['name'], task['real_time']))
            await asyncio.sleep(task['real_time']+1)

            res = await self.request_mission(session, 'finishReadMission', {"missionId": str(task['missionId']),
                                                                            "readTime": task['real_time']})
            if not res or res['resultCode'] != 0 or res['resultData']['code'] != '0000':
                if res['resultCode'] != 0:
                    reason = res['resultMsg']
                else:
                    reason = res['resultData']['msg']
                println('{}, 任务:{}, 提交任务结果失败!原因:{}'.format(self.account, task['name'],  reason))
                continue

            params = {
                "missionId": str(task['missionId']),
                "riskDeviceInfo": "{}",
                "channelLv": "share_jrApp",
                "environment": "other"
            }
            res = await self.request(session, 'receiveGooseTaskReward', params)
            await asyncio.sleep(1)
            if not res or res['resultCode'] != 0 or res['resultData']['code'] != '0000':
                if res['resultCode'] != 0:
                    reason = res['resultMsg']
                else:
                    reason = res['resultData']['msg']
                println('{}, 任务:{}, 领取奖励失败, 原因:{}'.format(self.account, task['name'], reason))
                continue
            println('{}, 任务:{}, 领取奖励成功'.format(self.account, task['name']))

    @logger.catch
    async def to_daily_home(self, session):
        """
        进入天天提鹅首页
        :return:
        """
        println('{}, 正在获取首页数据...'.format(self.account))
        body = {
            "timeSign": 0,
            "environment": "jrApp",
            "riskDeviceInfo": "{}"
        }
        data = await self.request(session, 'toDailyHome', body)

        if data['resultCode'] != 0:
            println('{}, 无法获取首页数据!, 原因:{}'.format(self.account, data['resultMsg']))
            return False
        else:
            if data['resultData']['code'] != '0000':
                println('{}, 无法获取数据, 原因:{}'.format(self.account, data['resultData']['msg']))
                return False
            println('{}, 获取首页数据成功！'.format(self.account))
            return data['resultData']['data']

    @logger.catch
    async def to_withdraw(self, session):
        """
        收鹅蛋
        :param session:
        :return:
        """
        data = await self.to_daily_home(session)
        if not data:
            println('{}, 获取鹅蛋数据失败, 无法提取!'.format(self.account))
            return

        await asyncio.sleep(1)

        if data['grassEggTotal'] < 1:  # 篮子装满了再提取，避免频繁提取!
            println('{}, 当前篮子鹅蛋小于1个, 无法提取...'.format(self.account))
            return

        body = {
            "timeSign": 0,
            "environment": "jrApp",
            "riskDeviceInfo": "{}"
        }
        await asyncio.sleep(1)  # 避免请求过快，JD抛错误
        data = await self.request(session, 'toWithdraw', body)
        if data['resultCode'] != 0:
            println('{}, 无法收取鹅蛋, 原因:{}!'.format(self.account, data['resultMsg']))
            return

        if data['resultData']['code'] != '0000':
            println('{}, 收取鹅蛋失败, 原因:{}'.format(self.account, data['resultData']['msg']))
            return

        self.egg_num += data['resultData']['data']['eggTotal']
        println('{}, 收取鹅蛋:{}个!'.format(self.account, data['resultData']['data']['eggTotal']))
        println('{}, 当前等级:{}!'.format(self.account, data['resultData']['data']['userLevelDto']['levelName']))
        println('{}, 当前鹅蛋总数:{}个！'.format(self.account, data['resultData']['data']['userLevelDto']['userHaveEggNum']))

    @logger.catch
    async def to_exchange(self, session):
        """
        鹅蛋兑换积分
        :param session:
        :return:
        """
        data = await self.to_daily_home(session)
        if data['availableTotal'] < 10:
            println('{}, 当前可用鹅蛋小于10个, 无法兑换积分...'.format(self.account))
            return

        body = {
            "timeSign": 0,
            "environment": "jrApp",
            "riskDeviceInfo": "{}"
        }
        await asyncio.sleep(1)
        data = await self.request(session, 'toGoldExchange', body)

        if data['resultCode'] != 0:
            println('{}, 鹅蛋兑换积分失败, 原因:{}'.format(self.account, data['resultMsg']))
            return

        if data['resultData']['code'] != '0000':
            println('{}, 鹅蛋兑换积分失败, 原因:{}'.format(self.account, data['resultData']['msg']))
            return

        println('{}, 成功兑换积分:{}个!'.format(self.account, data['resultData']['data']['cnumber']))
        println('{}, 当前总积分:{}个！'.format(self.account, data['resultData']['data']['goldTotal']))

    @logger.catch
    async def query_integral(self, session):
        """
        查询当前可用积分
        :param session:
        :return:
        """

        data = await self.request(session, 'queryGoldExchange', {})
        if data['resultCode'] != 0 or data['resultData']['code'] != '0000':
            return 0
        else:
            return data['resultData']['data']['goldTotal']

    @logger.catch
    async def notify(self, session):
        """
        :return:
        """
        index_data = await self.to_daily_home(session)
        total_egg = index_data['availableTotal']
        total_integral = await self.query_integral(session)
        message = '\n【活动名称】天天提鹅\n【京东ID】{}\n【获得鹅蛋】{}\n【获得积分】{}\n【可用鹅蛋】{}\n【可用积分】{}\n'.format(
            self.account, self.egg_num, self.integral, total_egg, total_integral)

        self.message = message

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            task_list = await self.query_task_list(session)
            await self.do_task_list(session, task_list)
            data = await self.to_daily_home(session)
            await asyncio.sleep(1)
            if not data:
                println('{}, 无法获取首页数据， 退出程序...'.format(self.account))
                return
            await self.to_withdraw(session)
            await asyncio.sleep(1)
            await self.to_exchange(session)
            await asyncio.sleep(1)
            #await self.notify(session)


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JrDailyTakeGoose, '天天提鹅')
