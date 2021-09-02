#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/25 9:29 上午
# @File    : jd_joy.py
# @Project : jd_scripts
# @Cron    : 45 8,12,17 * * *
# @Desc    : 京东APP->我的->宠汪汪
import asyncio
import hashlib
import json
import time

import aiohttp
import ujson
from utils.console import println
from urllib.parse import urlencode
from config import USER_AGENT
from utils.browser import open_page, open_browser, close_browser
from utils.logger import logger
from utils.jd_init import jd_init
from utils.validate import puzzle_validate_decorator


def md5(value):
    """
    md5加密
    :param value:
    :return:
    """
    obj = hashlib.md5()
    obj.update(value.encode())
    return obj.hexdigest()


@jd_init
@puzzle_validate_decorator
class JdJoy:
    """
    宠汪汪, 需要使用浏览器方式进行拼图验证。
    """
    # 活动地址
    url = 'https://h5.m.jd.com/babelDiy/Zeus/2wuqXrZrhygTQzYA7VufBEpj4amH/index.html#/pages/jdDog/jdDog'

    headers = {
        "Accept": "application/json,text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-cn",
        "Connection": "keep-alive",
        'lks': 'db0e24252b4d20349e3bf25eeef74e96',
        "Referer": "https://h5.m.jd.com/babelDiy/Zeus/2wuqXrZrhygTQzYA7VufBEpj4amH/index.html",
        'origin': 'https://h5.m.jd.com',
        "User-Agent": USER_AGENT
    }

    browser = None  # 浏览器对象
    page = None  # 页面标签对象

    @logger.catch
    async def validate(self, validator_selector='#app > div > div > div > div.man-machine > div.man-machine-container'):
        """
        拼图验证
        :return:
        """
        cookies = [
            {
                'domain': '.jd.com',
                'name': 'pt_pin',
                'value': self.cookies.get('pt_pin'),
            },
            {
                'domain': '.jd.com',
                'name': 'pt_key',
                'value': self.cookies.get('pt_key'),
            }
        ]
        if not self.browser:
            self.browser = await open_browser()
        if not self.page:
            self.page = await open_page(self.browser, self.url, USER_AGENT, cookies)

        try:
            return await self.puzzle_validate(self.page, validator_selector)
        except Exception as e:
            logger.error(e.args)
            return False

    async def request(self, session, path, body=None, method='GET', post_type='json'):
        """
        请求数据
        :param session:
        :param method:
        :param path:
        :param post_type:
        :param body:
        :return:
        """
        try:
            lkt = str(int(time.time()*1000))
            lks = md5('JL1VTNRadM68cIMQ' + lkt)
            session.headers['lks'] = lks
            session.headers['lkt'] = lkt

            default_params = {
                'reqSource': 'h5',
                'invokeKey': 'JL1VTNRadM68cIMQ'
            }
            if method == 'GET' and body:
                default_params.update(body)

            url = 'https://jdjoy.jd.com/common/{}'.format(path) + '?' + urlencode(default_params)

            if method == 'GET':
                response = await session.get(url)
            else:
                if post_type == 'json':
                    content_type = session.headers.get('Content-Type', None)
                    if content_type:
                        session.headers.pop('Content-Type')
                    response = await session.post(url, json=body)
                else:
                    session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
                    response = await session.post(url, data=body)

            text = await response.text()
            data = json.loads(text)

            if not data['errorCode']:
                if 'data' in data:
                    return data['data']
                elif 'datas' in data:
                    return data['datas']
                return data

            if data['errorCode'] == 'H0001':  # 需要拼图验证
                println('{}, 等待进行拼图验证!'.format(self.account))
                for i in range(3):
                    is_success = await self.validate()
                    if is_success:
                        return await self.request(session, path, body, method)

            return data

        except Exception as e:
            println('{}, 获取服务器数据失败:{}'.format(self.account, e.args))
            return {
                'errorCode': 9999
            }

    async def sign_every_day(self, session, task):
        """
        每日签到
        """
        println('{}, 签到功能暂时未完成!'.format(self.account))

    @logger.catch
    async def get_award(self, session, task):
        """
        领取任务奖励狗粮
        """
        path = 'pet/getFood'
        body = {
            'taskType': task['taskType']
        }
        data = await self.request(session, path, body)

        if not data or (data['errorCode'] and 'fail' in data['errorCode']):
            println('{}, 领取任务: 《{}》 奖励失败!'.format(self.account, task['taskName']))
        else:
            println('{}, 成功领取任务: 《{}》 奖励!'.format(self.account, task['taskName']))

    @logger.catch
    async def scan_market(self, session, task):
        """
        逛会场
        """
        market_list = task['scanMarketList']
        path = 'pet/scan'
        for market in market_list:
            market_link = market['marketLink']
            if market_link == '':
                market_link = market['marketLinkH5']
            params = {
                'marketLink': market_link,
                'taskType': task['taskType']
            }
            data = await self.request(session, path, params, method='POST')
            if not data or (data['errorCode'] and 'success' not in data['errorCode']):
                println('{}, 无法完成逛会场任务:{}!'.format(self.account, market['marketName']))
            else:
                println('{}, 成功完成逛会场任务:{}!'.format(self.account, market['marketName']))
            await asyncio.sleep(3)

    @logger.catch
    async def follow_shop(self, session, task):
        """
        关注店铺
        """
        click_path = 'pet/icon/click'
        shop_list = task['followShops']
        for shop in shop_list:
            click_params = {
                'iconCode': 'follow_shop',
                'linkAddr': shop['shopId']
            }
            await self.request(session, click_path, click_params)
            await asyncio.sleep(0.5)

            follow_path = 'pet/followShop'
            follow_params = {
                'shopId': shop['shopId']
            }
            data = await self.request(session, follow_path, follow_params, post_type='body', method='POST')
            if not data or 'success' not in data:
                println('{}, 无法关注店铺{}'.format(self.account, shop['name']))
            else:
                println('{}, 成功关注店铺: {}'.format(self.account, shop['name']))
            await asyncio.sleep(1)

    @logger.catch
    async def follow_good(self, session, task):
        """
        关注商品
        """
        path = 'pet/icon/click'
        good_list = task['followGoodList']

        for good in good_list:
            params = {
                'iconCode': 'follow_good',
                'linkAddr': good['sku']
            }
            await self.request(session, path, params)
            await asyncio.sleep(1)

            follow_path = 'pet/followGood'
            params = {
                'sku': good['sku']
            }
            data = await self.request(session, follow_path, params, method='POST', post_type='form')
            if not data:
                println('{}, 关注商品:{}失败!'.format(self.account, good['skuName']))
            else:
                println('{}, 成功关注商品:{}!'.format(self.account, good['skuName']))

    @logger.catch
    async def follow_channel(self, session, task):
        """
        """
        channel_path = 'pet/getFollowChannels'
        channel_list = await self.request(session, channel_path)
        if not channel_list:
            println('{}, 获取频道列表失败!'.format(self.account))
            return

        for channel in channel_list:
            if channel['status']:
                continue
            click_path = 'pet/icon/click'
            click_params = {
                'iconCode': 'follow_channel',
                'linkAddr': channel['channelId']
            }
            await self.request(session, click_path, click_params)
            follow_path = 'pet/scan'
            follow_params = {
                'channelId': channel['channelId'],
                'taskType': task['taskType']
            }
            data = await self.request(session, follow_path, follow_params, method='POST')
            await asyncio.sleep(0.5)
            if not data or (
                    data['errorCode'] and 'success' not in data['errorCode'] and 'repeat' not in data['errorCode']):
                println('{}, 关注频道:{}失败!'.format(self.account, channel['channelName']))
            else:
                println('{}, 成功关注频道:{}!'.format(self.account, channel['channelName']))
            await asyncio.sleep(3.1)

    @logger.catch
    async def do_task(self, session):
        """
        做任务
        :return:
        """
        path = 'pet/getPetTaskConfig'
        task_list = await self.request(session, path)
        if not task_list:
            println('{}, 获取任务列表失败!'.format(self.account))
            return
        for task in task_list:
            if task['receiveStatus'] == 'unreceive':
                await self.get_award(session, task)
                await asyncio.sleep(1)

            if task['joinedCount'] and task['joinedCount'] >= task['taskChance']:
                println('{}, 任务:{}今日已完成!'.format(self.account, task['taskName']))
                continue

            if task['taskType'] == 'SignEveryDay':
                await self.sign_every_day(session, task)

            elif task['taskType'] == 'FollowGood':  # 关注商品
                await self.follow_good(session, task)

            elif task['taskType'] == 'FollowChannel':  # 关注频道
                await self.follow_channel(session, task)

            elif task['taskType'] == 'FollowShop':  # 关注店铺
                await self.follow_shop(session, task)

            elif task['taskType'] == 'ReserveSku':  # 商品预约
                println('{}, 无法执行任务:《预约{}》!'.format(self.account, task.get('taskName')))

            elif task['taskType'] == 'ScanMarket':  # 逛会场
                await self.scan_market(session, task)

    @logger.catch
    async def get_friend_list(self, session, page=1):
        """
        获取好友列表
        """
        path = 'pet/h5/getFriends'
        params = {
            'itemsPerPage': 20,
            'currentPage': page
        }
        friend_list = await self.request(session, path, params)
        if not friend_list:
            return []
        return friend_list

    @logger.catch
    async def help_friend_feed(self, session, count=1):
        """
        帮好友喂狗
        """
        cur_page = 0
        cur_count = 1
        while True:
            cur_page += 1
            friend_list = await self.get_friend_list(session, page=cur_page)
            if not friend_list:
                break

            for friend in friend_list:
                if cur_count > count:
                    break
                if friend['status'] == 'chance_full':
                    println('{}, 今日帮好友喂狗次数已用完成!'.format(self.account))
                    return

                if friend['status'] != 'not_feed':
                    continue

                feed_path = 'pet/helpFeed'
                feed_params = {
                    'friendPin': friend['friendPin']
                }
                data = await self.request(session, feed_path, feed_params)
                if data and data['errorCode'] and 'ok' in data['errorCode']:
                    println('{}, 成功帮好友:{} 喂狗!'.format(self.account, friend['friendName']))
                    cur_count += 1
                else:
                    println('{}, 无法帮好友:{}喂狗!'.format(self.account, friend['friendName']))
                    error_code = data.get('errorCode', '')
                    if 'full' in error_code or 'insufficient' in error_code:
                        break
                await asyncio.sleep(1)
            await asyncio.sleep(1)

    @logger.catch
    async def joy_race(self, session, level=2):
        """
        参与赛跑
        """
        println('{}, 领取赛跑奖励!'.format(self.account))
        reward_path = 'pet/combat/receive'
        await self.request(session, reward_path)
        await asyncio.sleep(0.5)

        click_path = 'pet/icon/click'
        click_params = {
            'iconCode': 'race_match',
        }
        println('{}, 正在匹配对手!'.format(self.account))
        await self.request(session, click_path, click_params)
        await asyncio.sleep(0.5)

        match_path = 'pet/combat/match'
        match_params = {
            'teamLevel': level
        }

        for i in range(10):
            data = await self.request(session, match_path, match_params)
            if data['petRaceResult'] == 'participate':
                println('{}, 成功参与赛跑!'.format(self.account))
                return
            await asyncio.sleep(1)
        println('{}, 无法参与赛跑!'.format(self.account))

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:
            await self.do_task(session)
            await self.joy_race(session)
            await self.help_friend_feed(session)

        await close_browser(self.browser)


if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = JdJoy(**JD_COOKIES[0])
    # asyncio.run(app.run())
    from utils.process import process_start
    from config import JOY_PROCESS_NUM
    process_start(JdJoy, '宠汪汪做任务', process_num=JOY_PROCESS_NUM)
