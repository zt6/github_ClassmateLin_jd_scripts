#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/20 2:25 下午
# @File    : jd_supermarket.py
# @Project : jd_scripts
# @Cron    : 7 7,20 * * *
# @Desc    : 京东APP首页->京东超市->游戏
import asyncio
import json
import time

import aiohttp
from urllib.parse import urlencode
from config import USER_AGENT
from utils.jd_init import jd_init
from utils.console import println
from utils.logger import logger


@jd_init
class JdSupermarket:
    """
    东东超市
    """

    headers = {
        'origin': 'https://jdsupermarket.jd.com',
        'user-agent': USER_AGENT,
        'referer': 'https://jdsupermarket.jd.com/game/?tt={}'.format(int(time.time() * 1000)),
        'content-type': 'application/x-www-form-urlencoded',
    }

    @logger.catch
    async def request(self, session, function_id, body=None, method='GET'):
        """
        请求数据
        :param method:
        :param body:
        :param function_id:
        :param session:
        :return:
        """
        try:
            if not body:
                body = {"channel": "1"}
            else:
                body
            params = {
                'functionId': function_id,
                'appid': 'jdsupermarket',
                'clientVersion': '8.0.0',
                'client': 'm',
                't': int(time.time()),
                'body': json.dumps(body)
            }
            url = 'https://api.m.jd.com/api?' + urlencode(params)

            if method == 'GET':
                response = await session.get(url)
            else:
                response = await session.post(url)

            text = await response.text()

            data = json.loads(text)

            if data.get('code') == 0:
                return data['data']
            else:
                return {
                    'bizCode': data['code'],
                    'bizMsg': data['msg'],
                }

        except Exception as e:
            println('{}, 请求数据失败, {}!'.format(self.account, e.args))
            return {
                'bizCode': 9999,
                'bizMsg': '请求服务器数据失败',
            }

    @logger.catch
    async def sign(self, session):
        """
        签到
        :return:
        """
        res = await self.request(session, 'smtg_signList')
        if res.get('bizCode') != 0:
            println('{}, 查询签到数据失败!'.format(self.account))
            return

        if res.get('result', dict()).get('hadSigned', 0) == 1:
            println('{}, 今日已签到, 无需再次签到!'.format(self.account))
            return

        await asyncio.sleep(0.5)

        data = await self.request(session, 'smtg_sign')
        code = data.get('bizCode')
        if code == 0:
            msg = '签到成功, 获得{}京豆!'.format(data.get('result', dict()).get('jdBeanCount', 0))
        elif code == 811:
            msg = '今日已签到!'
        else:
            msg = '签到失败!'

        println('{}, {}'.format(self.account, msg))

    @logger.catch
    async def receive_money(self, session):
        """
        收取营业额
        :param session:
        :return:
        """
        res = await self.request(session, 'smtg_receiveCoin', {'type': 4})
        if res.get('bizCode') != 0:
            println('{}, 收取营业额失败!'.format(self.account))
            return

        println('{}, 成功收取营业额!'.format(self.account))

    @logger.catch
    async def do_tasks(self, session, output=True):
        """
        做任务
        :return:
        """
        res = await self.request(session, 'smtg_queryShopTask')
        if res.get('bizCode', -1) != 0:
            println('{}, 无法获取任务列表!'.format(self.account))
            return

        task_list = res['result']['taskList']

        for task in task_list:
            task_name, task_type = task['title'], task['type']
            if task['prizeStatus'] == 1:  # 奖励待领取
                res = await self.request(session, 'smtg_obtainShopTaskPrize', {'taskId': task['taskId']})
                if res.get('bizCode') == 0:
                    println('{}, 成功领取任务:《{}》奖励, 获得蓝币:{}!'.format(self.account,
                                                               task_name, res['result']['blueCoin']))

            if task['taskStatus'] == 1:  # 任务已完成
                if output:
                    println('{}, 任务:《{}》今日已完成!'.format(self.account, task_name))
                continue

            if task_type in [2, 8, 10]:
                done_num = task['finishNum']
                target_num = task['targetNum']
                item_id = list(task['content'].values())[0]['itemId']
                res = await self.request(session, 'smtg_doShopTask', {'taskId': task['taskId'], 'itemId': item_id})
                if res.get('bizCode') == 0:
                    println('{}, 成功完成任务《{}》, {}/{}!'.format(self.account, task_name, done_num + 1, target_num))
                if done_num < target_num:
                    await asyncio.sleep(1)
                    await self.do_tasks(session, output=False)
                else:
                    break
            else:
                if output:
                    println('{}, 跳过任务：《{}》!'.format(self.account, task_name))

    @logger.catch
    async def get_home_data(self, session):
        """
        获取店铺升级奖励
        :param session:
        :return:
        """
        res = await self.request(session, 'smtg_newHome')
        if res.get('bizCode') != 0:
            println('{}, 获取首页数据失败!'.format(self.account))
            return None
        return res['result']

    @logger.catch
    async def upgrade(self, session):
        """
        升级货架
        :param session:
        :return:
        """
        res = await self.request(session, 'smtg_shopIndex')
        if res.get('bizCode') != 0:
            println('{}, 获取店铺数据失败!'.format(self.account))
            return
        data = res['result']
        shop_id = data['shopId']
        shelf_list = data['shelfList']
        shelf_id = None
        shelf_level = 0
        shelf_name = None

        for shelf in shelf_list:
            if shelf['status'] == 1:
                shelf_id = shelf['id']
                shelf_level = shelf['level'] + 1
                shelf_name = shelf['name']
                break

        if shelf_id:  # 有可以升级的货架
            res = await self.request(session, 'smtg_shelfUpgrade', {
                "shopId": shop_id, "shelfId": shelf_id, "targetLevel": shelf_level})
            if res.get('bizCode') == 0:
                println('{}, 成功升级:{}, 当前等级:{}!'.format(self.account, shelf_name, shelf_level))

    @logger.catch
    async def get_upgrade_award(self, session):
        """
        获取店铺升级奖励
        :param session:
        :return:
        """
        data = await self.get_home_data(session)
        if not data:
            return

        item_list = data.get('userUpgradeBlueVos', [])

        if not item_list:
            println('{}, 暂无店铺升级奖励可领!'.format(self.account))

        for item in item_list:
            res = await self.request(session, 'smtg_receiveCoin', {'type': 5, 'id': item['id']})
            if res.get('bizCode') == 0:
                println('{}, 成功收取:{}蓝币!'.format(self.account, item['blueCoins']))
            await asyncio.sleep(1)

    async def receive_coin(self, session, coin_type=2):
        """
        收顾客头上的蓝币
        :param session:
        :param coin_type:
        :return:
        """
        res = await self.request(session, 'smtg_receiveCoin', {"type": coin_type, "channel": "1"})
        if res.get('bizCode') == 0:
            println('{}, 成功收取蓝币:{}!'.format(self.account, res['result']['receivedBlue']))

    @logger.catch
    async def run(self):
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            home_data = await self.get_home_data(session)
            if not home_data:
                println('{}, 由于无法获取首页数据, 退出程序...'.format(self.account))
                return
            await self.sign(session)
            await self.upgrade(session)
            await self.receive_coin(session)
            await self.receive_money(session)
            await self.get_upgrade_award(session)
            await self.do_tasks(session)


if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = JdSupermarket(**JD_COOKIES[6])
    # asyncio.run(app.run())
    from utils.process import process_start
    process_start(JdSupermarket, '东东超市')
