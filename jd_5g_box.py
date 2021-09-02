#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 下午7:45
# @Project : jd_scripts
# @File    : jd_5g_box.py
# @Cron    : 8 0 * * *
# @Desc    : 京东APP->营业厅->领京豆, 5G盲盒做任务抽奖
import asyncio
import json
import time

import aiohttp
from urllib.parse import urlencode

from config import USER_AGENT
from utils.console import println
from utils.logger import logger
from utils.jd_init import jd_init
from db.model import Code
from utils.process import process_start

# 5G盲盒助力码
CODE_5G_BOX = 'jd_5g_box'


@jd_init
class Jd5GBox:
    """
    5G盲盒
    """
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': USER_AGENT,
        'referer': 'https://blindbox5g.jd.com',
    }

    @logger.catch
    async def request(self, session, body=None, method='POST'):
        """
        请求数据
        :param session:
        :param body:
        :param method:
        :return:
        """
        try:

            if not body:
                body = {}
            params = {
                'appid': 'blind-box',
                'functionId': 'blindbox_prod',
                'body': json.dumps(body),
                't': int(time.time()),
                'loginType': 2,
            }
            url = 'https://api.m.jd.com/api?' + urlencode(params)

            if method == 'POST':
                response = await session.post(url)
            else:
                response = await session.get(url)

            text = await response.text()

            data = json.loads(text)

            return data

        except Exception as e:
            println('{}, 请求数据失败, {}'.format(self.account, e.args))

    @logger.catch
    async def get_coin(self, session):
        """
        收信号值
        :param session:
        :return:
        """
        res = await self.request(session, {"apiMapping": "/active/getCoin"})
        if res.get('code') == 200:
            println('{}, 成功收取信号值:{}'.format(self.account, res.get('data')))
        else:
            println('{}, 收取信号值失败,{}'.format(self.account, res.get('msg')))

    @logger.catch
    async def do_tasks(self, session, n=11):
        """
        做任务
        :param n:
        :param session:
        :return:
        """
        if n < 0:
            return
        res = await self.request(session, {"apiMapping": "/active/taskList"})
        if res.get('code') != 200:
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        flag = False
        task_list = list(res['data'].values())
        for task in task_list:

            if task['finishNum'] >= task['totalNum']:  # 已完成任务
                continue

            task_type = task['type']

            if task_type in [5, 8]:  # 跳过充值任务
                continue
            elif task_type == 4:  # 浏览商品
                flag = True
                await self.request(session, {"skuId": task['skuId'], "apiMapping": "/active/browseProduct"})
                println('{}, 浏览商品:{}!'.format(self.account, task['skuId']))

            elif task_type == 2:
                res = await self.request(session, {"shopId": task['shopId'], "apiMapping": "/active/followShop"})
                println('{}, 关注店铺:{}, 获得信号值:{}, 京豆:{}'.format(self.account,
                                                              task['shopId'], res['data']['coinNum'],
                                                              res['data']['jbeanNum']))

            elif task_type == 1:  # 浏览会场
                flag = True
                await self.request(session, {"activeId": task['activeId'], "apiMapping": "/active/strollActive"})
                println('{}, 浏览会场:{}！'.format(self.account, task['activeId']))

        if flag:
            println('{}, 8秒后领取任务奖励!'.format(self.account))
            await asyncio.sleep(8)

            for task in task_list:
                task_type = task['type']
                if task_type in [2, 8, 5]:  # 跳过充值任务
                    continue

                res = await self.request(session, {"type": task['type'], "apiMapping": "/active/taskCoin"})
                if res.get('code') == 200:
                    println('{}, 成功领取任务奖励, 信号值{}, 京豆{}!'.format(self.account,
                                                                res['data']['coinNum'], res['data']['jbeanNum']))
                else:
                    println('{}, 无法领取任务奖励, {}!'.format(self.account, res.get('msg')))
                await asyncio.sleep(1)

        await self.do_tasks(session, n - 1)

    @logger.catch
    async def get_share_code(self, session):
        """
        :return:
        """
        res = await self.request(session, {"apiMapping": "/active/shareUrl"})
        if res.get('code') != 200:
            return
        code = res.get('data')
        println('{}, 助力码:{}'.format(self.account, code))
        Code.insert_code(code_key=CODE_5G_BOX, code_val=code, sort=self.sort, account=self.account)

    @logger.catch
    async def run_help(self):
        """
        助力入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            item_list = Code.get_code_list(CODE_5G_BOX)
            for item in item_list:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue

                res = await self.request(session, {"shareId": code, "apiMapping": "/active/addShare"})
                if res.get('code') == 200:
                    println('{}, 成功助力好友:{}'.format(self.account, account))
                else:
                    println('{}, 无法助力好友:{}, {}'.format(self.account, account, res.get('msg')))
                    if res.get('code') == 2005:
                        break

                await asyncio.sleep(1)

    @logger.catch
    async def browse_goods(self, session):
        """
        浏览精彩好物
        :param session:
        :return:
        """
        res = await self.request(session, {"apiMapping": "/active/conf"})
        if res.get('code') != 200:
            println('{}, 获取精彩好物列表失败!'.format(self.account))
            return

        item_list = res['data']['skuList']

        for item in item_list:
            if item['state'] == 2:  # 已完成
                continue
            await self.request(session, {"type": 0, "id": item['id'], "apiMapping": "/active/homeGoBrowse"})
            await asyncio.sleep(1)
            res = await self.request(session, {"type": 0, "id": item['id'], "apiMapping": "/active/taskHomeCoin"})
            if res.get('code') == 200:
                println('{}, 浏览商品:{}, 获得200信号值!'.format(self.account, item['name']))
            await asyncio.sleep(1)

    @logger.catch
    async def lottery(self, session):
        """
        抽奖
        :param session:
        :return:
        """
        while True:
            res = await self.request(session, {"apiMapping": "/prize/lottery"})
            if res.get('code') != 200:
                break
            else:
                println('{}, 奖品:{}'.format(self.account, res['data']['name']))
            await asyncio.sleep(1)

    @logger.catch
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.get_coin(session)  # 收取信号值
            await self.get_share_code(session)  # 获取助力码
            await self.do_tasks(session)  # 做任务
            await self.browse_goods(session)  # 浏览精彩好物
            await self.lottery(session)  # 抽奖


if __name__ == '__main__':
    process_start(Jd5GBox, '5G盲盒', code_key=CODE_5G_BOX)
