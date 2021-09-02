#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/23 下午6:54
# @Project : jd_scripts
# @File    : jx_pasture.py
# @Cron    : 35 6,16 * * *
# @Desc    : 京喜APP->京喜牧场->日常任务
import json
import random
import time
from datetime import datetime
from urllib.parse import urlencode

import aiohttp
import asyncio

from config import USER_AGENT

from utils.jx_init import jx_init, md5
from utils.logger import logger
from utils.console import println
from utils.jx_pasture_token import get_token
from utils.process import process_start, get_code_list
from db.model import Code


# 京喜牧场
CODE_JX_PASTURE = 'jd_pasture'


def generate_str(length=16):
    """
    生成随机字符串
    :param length:
    :return:
    """
    s = 'abcdefghijklmnopqrstuvwxyz1234567890'
    return ''.join(random.sample(s, length))


@jx_init
class JxPasture:
    headers = {
        'user-agent': USER_AGENT.replace('jdapp;', 'jdpingou;'),
        'referer': 'https://st.jingxi.com/'
    }

    coins = 0  # 金币数量
    food_num = 0  # 白菜数量
    active_id = ''  # 活动ID
    pet_info_list = None  # 小鸡相关信息列表
    cow_info = None  # 牛相关信息
    share_code = None  # 助力码
    phone_id = None  # 设备ID
    egg_num = 0  # 金蛋数量

    newcomer_task_step = ['A-1', 'A-2',  'A-3', 'A-4', 'A-5', 'A-6', 'A-7', 'A-8', 'A-9',
                          'A-10', 'A-11', 'A-12', 'B-1', 'C-1', 'D-1', 'E-1', 'E-2', 'E-3', 'E-4', 'E-5',
                          'F-1', 'F-2', 'G-1', 'G-2', 'G-3', 'G-4', 'G-5', 'G-6', 'G-7', 'G-8', 'G-9']

    async def request(self, session, path, body=None, method='GET'):
        """
        请求数据
        :param session:
        :param body:
        :param path:
        :param params:
        :param method:
        :return:
        """
        try:
            if not self.phone_id:
                self.phone_id = generate_str()
            timestamp = str(int(time.time() * 1000))
            js_token = md5(self.account + timestamp + self.phone_id + 'tPOamqCuk9NLgVPAljUyIHcPRmKlVxDy')
            time_ = datetime.now()
            params = {
                'channel': '7',
                'sceneid': '1001',
                'activeid': self.active_id,
                'activekey': 'null',
                '_ste': '1',
                '_': int(time_.timestamp() * 1000) + 2,
                'sceneval': '2',
                'g_login_type': '1',
                'callback': '',
                'g_ty': 'ls',
                'jxmc_jstoken': js_token
            }
            if not body:
                body = dict()
            params.update(body)
            url = 'https://m.jingxi.com/{}?'.format(path) + urlencode(params)
            h5st = await self.encrypt(time_, url)
            url += '&h5st=' + h5st
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)

            text = await response.text()
            data = json.loads(text)
            return data
        except Exception as e:
            println(e.args)

    async def get_home_data(self, session):
        """
        获取首页数据
        :param session:
        :return:
        """
        println('{}, 获取首页数据!'.format(self.account))
        body = {
            'isgift': 1,
            'isquerypicksite': 1,
            '_stk': 'activeid,activekey,channel,isgift,isquerypicksite,sceneid'
        }
        res = await self.request(session, 'jxmc/queryservice/GetHomePageInfo', body)
        if res.get('ret') != 0:
            return None
        else:
            return res.get('data')

    async def get_gold_from_bull(self, session):
        """
        收牛的金币
        :param session:
        :return:
        """
        res = await self.request(session, 'jxmc/operservice/GetCoin', {
            '_stk': 'activeid,activekey,channel,jxmc_jstoken,phoneid,sceneid,timestamp,token',
            'token': get_token(self.cow_info['lastgettime'])
        })

        if res.get('ret') == 0:
            println('{}, 成功收牛牛, 获得金币:{}'.format(self.account, res['data']['addcoin']))
        else:
            println('{}, 收取牛牛失败, {}'.format(self.account, res.get('message')))

    async def sign(self, session):
        """
        签到
        :param session:
        :return:
        """
        res = await self.request(session, 'jxmc/queryservice/GetSignInfo', {
            '_stk': 'activeid,activekey,channel,sceneid'
        })

        if res.get('ret') != 0:
            println('{}, 获取签到数据失败, {}!'.format(self.account, res.get('message')))
            return

        for item in res['data']['signlist']:
            if not item['fortoday']:
                continue
            if item['hasdone']:
                println('{}, 今日已签到!'.format(self.account))
                continue

            res = await self.request(session, 'jxmc/operservice/GetSignReward', {
                '_stk': 'channel,currdate,sceneid',
                'currdate': res['data']['currdate']
            })
            if res.get('ret') == 0:
                println('{}, 签到成功!'.format(self.account))
            else:
                println('{}, 签到失败, {}'.format(self.account, res.get('message')))

    async def init(self, session):
        """
        初始化
        :param session:
        :return:
        """
        home_data = await self.get_home_data(session)
        if not home_data:
            return False

        self.coins = home_data.get('coins', 0)
        self.active_id = home_data.get('activeid', '')
        self.pet_info_list = home_data.get('petinfo', [])
        self.share_code = home_data.get('sharekey')
        self.cow_info = home_data.get('cow')
        self.egg_num = home_data.get('eggcnt')

        cur_task_step = home_data.get('finishedtaskId')

        if cur_task_step in self.newcomer_task_step:
            await self.do_newcomer_task(session, cur_task_step)

        try:
            self.food_num = home_data.get('materialinfo', list())[0]['value']
        except Exception as e:
            println('{}, 活动未开启!'.format(self.account, e.args))
            await self.do_newcomer_task(session)

        return True

    async def buy_food(self, session):
        """
        买白菜
        :return:
        """
        while self.food_num <= 500 and self.coins >= 5000:
            res = await self.request(session, 'jxmc/operservice/Buy', {
                '_stk': 'activeid,activekey,channel,jxmc_jstoken,phoneid,sceneid,timestamp,type',
                'type': 1
            })
            if res.get('ret') == 200:
                self.coins -= 5000
                self.food_num += 100
                println('{}, 成功购买一次白菜!'.format(self.account))
            else:
                break

    async def feed(self, session):
        """
        投喂小鸡
        :param session:
        :return:
        """
        if self.food_num < 10:
            println('{}, 当前白菜不足10颗, 无法投喂小鸡!'.format(self.account))
            return

        while self.food_num >= 10:
            res = await self.request(session, 'jxmc/operservice/Feed', {
                '_stk': 'activeid,activekey,channel,jxmc_jstoken,phoneid,sceneid,timestamp'
            })
            if res.get('ret') == 0:
                println('{}, 成功投喂一次小鸡'.format(self.account))
                self.food_num = res['data']['newnum']
            elif res.get('ret') == 2020 and res['data']['maintaskId'] == 'pause':
                res = await self.request(session, 'jxmc/operservice/GetSelfResult', {
                    '_stk': 'channel,itemid,sceneid,type',
                    'petid': self.pet_info_list[0]['petid'],
                    'type': 11
                })
                if res.get('ret') == 0:
                    println('{}, 成功收取一枚金蛋, 当前金蛋:{}'.format(self.account, res['data']['newnum']))
            else:
                println('{}, 投喂失败, {}'.format(self.account, res.get('message')))
                break
            println('{}, 5秒后进行一次投喂小鸡!'.format(self.account))
            await asyncio.sleep(5)

    @logger.catch
    async def mowing(self, session, max_times=10):
        """
        割草
        :param max_times:
        :param session:
        :return:
        """
        for i in range(1, max_times + 1):
            res = await self.request(session, 'jxmc/operservice/Action', {
                '_stk': 'activeid,activekey,channel,jxmc_jstoken,phoneid,sceneid,timestamp,type',
                'type': 2
            })
            if res.get('ret') != 0:
                println('{}, 第{}次割草失败, {}!'.format(self.account, i, res.get('message')))
                break

            println('{}, 第{}次割草成功, 获得金币:{}'.format(self.account, i, res['data']['addcoins']))

            if res.get('data', dict()).get('surprise'):
                await asyncio.sleep(2)
                award_res = await self.request(session, 'jxmc/operservice/GetSelfResult', {
                    '_stk': 'activeid,activekey,channel,sceneid,type',
                    'type': 14
                })
                if award_res.get('ret') == 0:
                    println('{}, 获得割草奖励, {}'.format(self.account, award_res['data']['prizepool']))

            if i + 1 <= max_times:
                println('{}, 2s后进行第{}次割草!'.format(self.account, i + 1))
                await asyncio.sleep(2)

    async def sweep_chicken_legs(self, session, max_times=10):
        """
        扫鸡腿
        :return:
        """
        for i in range(1, max_times + 1):
            res = await self.request(session, 'jxmc/operservice/Action', {
                '_stk': 'activeid,activekey,channel,petid,sceneid,type',
                'type': 1,
                'petid': self.pet_info_list[0]['petid']
            })
            if res.get('ret') != 0:
                println('{}, 第{}次扫鸡腿失败, {}'.format(self.account, i, res.get('message')))
                break
            println('{}, 第{}次扫鸡腿成功, 获得金币:{}'.format(self.account, i, res['data']['addcoins']))

            if i + 1 <= max_times:
                println('{}, 5s后进行第{}次扫鸡腿!'.format(self.account, i + 1))
                await asyncio.sleep(5)

    async def do_tasks(self, session, max_times=10):
        """
        做任务和领奖
        :return:
        """
        for i in range(max_times):
            break_flag = False
            res = await self.request(session, '/newtasksys/newtasksys_front/GetUserTaskStatusList', {
                'source': 'jxmc',
                'bizCode': 'jxmc',
                'dateType': '',
                'showAreaTaskFlag': 0,
                'jxpp_wxapp_type': 7,
                '_stk': 'bizCode,dateType,jxpp_wxapp_type,showAreaTaskFlag,source',
                'gty': 'ajax'
            })
            if res.get('ret') != 0:
                println('{}, 获取每日任务列表失败!'.format(self.account))
                return
            item_list = res['data']['userTaskStatusList']
            for item in item_list:
                task_type, task_name = item['taskType'], item['taskName']

                if item['awardStatus'] == 1:  # 奖励已领取
                    continue

                break_flag = False
                if item['completedTimes'] >= item['targetTimes']:
                    res = await self.request(session, '/newtasksys/newtasksys_front/Award', {
                        'source': 'jxmc',
                        'bizCode': 'jxmc',
                        'taskId': item['taskId'],
                        '_stk': 'bizCode,source,taskId',
                        'gty': 'ajax'
                    })
                    if res.get('ret') == 0:
                        println('{}, 成功领取任务《{}》奖励!'.format(self.account, item['taskName']))
                    await asyncio.sleep(2)

                if task_type == 2:
                    res = await self.request(session, '/newtasksys/newtasksys_front/DoTask', {
                        'source': 'jxmc',
                        'bizCode': 'jxmc',
                        'taskId': item['taskId'],
                        'configExtra': '',
                        '_stk': 'bizCode,configExtra,source,taskId',
                        'gty': 'ajax'
                    })
                    if res.get('ret') == 0:
                        println('{}, 成功完成任务:{}'.format(self.account, task_name))

                await asyncio.sleep(2)
            if break_flag:
                break

    async def run_help(self):
        """
        :return:
        """
        await self.get_encrypt()
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            if not await self.init(session):
                println('{}, 无法初始化, 退出程序!'.format(self.account))
                return
            item_list = Code.get_code_list(code_key=CODE_JX_PASTURE)
            item_list.extend(get_code_list(CODE_JX_PASTURE))
            for item in item_list:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue
                res = await self.request(session, '/jxmc/operservice/EnrollFriend', {
                    'sharekey': code,
                    '_stk': 'channel,sceneid,sharekey'
                })
                if res.get('ret') == 0:
                    println('{}, 成功助力好友:{}'.format(self.account, account))
                else:
                    println('{}, 助力好友:{}失败, {}'.format(self.account, account, res.get('message')))
                await asyncio.sleep(3)

    async def get_can_exchange_goods(self, session):
        """
        获取可兑换商品列表
        :param session:
        :return:
        """
        awards = []

        res = await self.request(session, '/jxmc/queryservice/GetGoodsListV2', {
            '_stk': 'activeid,activekey,channel,sceneid'
        })
        if res.get('ret') != 0:
            println('{}, 获取可兑换商品列表失败!'.format(self.account))
            return awards

        prize_pools = dict()
        goods_list = res['data']['goodslist']

        for goods in goods_list:
            if self.egg_num >= goods['neednum']:
                prize_pools[goods['prizepool']] = goods['neednum']

        if not prize_pools:
            return awards

        url = 'https://m.jingxi.com/active/queryprizedetails?' + urlencode({
            'actives': ','.join(list(prize_pools.keys())),
            '_': int(time.time() * 1000),
            'sceneval': 2,
            'g_login_type': 2,
            'g_ty': 'ls'
        })
        response = await session.get(url)
        text = await response.text()

        text = text.replace('try{ QueryPrizesDetails(', '')
        text = text.replace(');}catch(e){}', '')
        res = json.loads(text)

        if res.get('retcode') != 0:
            println('{}, 获取可兑换奖品列表失败!'.format(self.account))
            return awards

        for item in res['result']:
            egg_num = prize_pools[item['active']]
            award_name = item['prizes'][0]['Name']
            awards.append('{}({}金蛋)'.format(award_name, egg_num))

        return awards

    async def notify(self, session):
        """
        获取金蛋数量及可兑换商品通知
        :return:
        """
        await self.init(session)  # 刷新首页数据

        self.message = '【活动名称】京喜牧场\n【京东账号】{}\n'.format(self.account)
        self.message += '【白菜数量】{}\n【金币数量】{}\n'.format(self.food_num, self.coins)
        self.message += '【金蛋数量】{}\n'.format(self.egg_num)
        self.message += '【当前可兑换商品】'

        await asyncio.sleep(1)
        awards = await self.get_can_exchange_goods(session)
        if not awards:
            self.message += '暂无/黑号/网络异常\n'

        for i in range(len(awards)):
            self.message += awards[i] + ', '
            if i + 1 % 4 == 0:
                self.message += '\n'

        self.message += '\n\n'

    async def get_daily_food(self, session):
        """
        每天领白菜
        :return:
        """
        res = await self.request(session, '/jxmc/operservice/GetVisitBackCabbage', {
            'timestamp': int(time.time()*1000),
            '_stk': 'activeid,activekey,channel,jxmc_jstoken,phoneid,sceneid,timestamp'
        })
        if res.get('ret') == 0:
            println('{}, 成功领取白菜!'.format(self.account))

    async def do_newcomer_task(self, session, cur_step='A-1'):
        """
        :return:
        """
        flag = False
        for step in self.newcomer_task_step:
            if cur_step == step:
                flag = True
            if flag:
                res = await self.request(session, '/jxmc/operservice/DoMainTask', {
                    'step': step,
                    'timestamp': int(time.time()*1000),
                    '_stk': 'activeid,activekey,channel,jxmc_jstoken,phoneid,sceneid,step,timestamp'
                })
                if res.get('ret') == 0:
                    println('{}, 完成新手任务:{}'.format(self.account, step))
                await asyncio.sleep(2)

    async def run(self):
        """
        :return:
        """
        await self.get_encrypt()
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            if not await self.init(session):
                println('{}, 无法初始化, 退出程序!'.format(self.account))
                return

            if self.share_code:
                println('{}, 助力码:{}'.format(self.account, self.share_code))
                Code.insert_code(code_key=CODE_JX_PASTURE, code_val=self.share_code, sort=self.sort,
                                 account=self.account)

            await self.get_daily_food(session)
            await self.sign(session)  # 每日签到
            await self.get_gold_from_bull(session)  # 收牛牛金币
            await self.buy_food(session)  # 购买白菜
            await self.feed(session)  # 喂食
            await self.mowing(session, max_times=20)  # 割草20次
            await self.sweep_chicken_legs(session, max_times=20)  # 扫鸡腿20次
            await self.do_tasks(session)  # 做任务领奖励
            await self.notify(session)  # 通知


if __name__ == '__main__':
    process_start(JxPasture, '京喜牧场', code_key=CODE_JX_PASTURE)
