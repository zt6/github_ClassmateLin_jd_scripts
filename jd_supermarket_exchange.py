#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @File         : jd_supermarket_exchange.py
# @Project      : jd_scripts
# @Created Date : 2021-09-18 22:30:12
# @Last Modified: 2021-09-19 21:32:19
# @Cron         : 59 23 * * *
# @Desc         : 京东APP首页->京东超市->游戏  0点兑换物品


import asyncio
from datetime import datetime
import time

import aiohttp
from dateutil.relativedelta import relativedelta
from utils.console import println
from utils.logger import logger
from jd_supermarket import JdSupermarket


class JdSupermarketExchange(JdSupermarket):
    """
    京东超时 0点 兑换商品(京豆/其它物品)
    """

    buy_limit = 1
    """购买限制
    """
    # 要兑换商品信息
    prize = None
    areaId = None
    periodId = None
    prizeId = None
    cost = 0 # 待兑换商品所需蓝币
    total_blue_coin = 0 # 用户蓝币数

    async def query_price(self, session, name):
        """
        查询商品数据
        """
        data = await self.request(session, 'smt_queryPrizeAreas')
        try:
            if data['bizCode'] != 0:
                println('{}, 无法获取商品列表!({})'.format(self.account,data.get('bizMsg')))
            for area in data['result']['areas']:
                prizes = area.get('prizes')
                if not prizes:
                    continue
                for prize in prizes:
                    if name in prize.get('name'):
                        println(f"{self.account},你兑换的商品信息: {prize['name']}")
                        # TODO: type = 4 && not beanType , smtg_lockMaterialPrize
                        self.prize = prize
                        self.areaId = area['areaId']
                        self.periodId = area['periodId']
                        self.prizeId = prize['prizeId']
                        self.cost = prize['cost']
                        break
                if self.prize:
                    break
            if not self.prize:
                println(f'{self.account},请检查你要兑换({JD_SUPERMARKET_EXCHANGE})的商品是否存在!')
        except Exception as e:
            println('{}, 无法获取商品列表! {} ({})'.format(self.account, e.args, data.get('bizMsg')))

    async def obtain_prize(self,session, functionId = 'smt_exchangePrize'):
        """
        兑换商品
        """
        body = {
            "connectId": self.prizeId,
            "areaId": self.areaId,
            "periodId": self.periodId,
            "informationParam": {
                "eid": "",
                "referUrl": -1,
                "shshshfp": "",
                "openId": -1,
                "isRvc": 0,
                "fp": -1,
                "shshshfpa": "",
                "shshshfpb": "",
                "userAgent": -1
            },
            "channel": "18"
        }
        data = await self.request(session, functionId, body)
        return data

    async def do_exchange(self, session):
        """
        整点开始兑换
        """
        if datetime.now().hour >= 23 and datetime.now().minute >= 58:
            start_time = datetime.strftime((datetime.now() + relativedelta(days=1)), "%Y-%m-%d 00:00:00")
        else:
            start_time = datetime.strftime((datetime.now()), "%Y-%m-%d 00:00:00")

        exchange_start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        exchange_start_timestamp = int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")) * 1000)

        while True:
            now = int(time.time()*1000)
            if now >= exchange_start_timestamp:
                println('{}, 当前时间({})大于兑换时间, 去兑换商品!'.format(self.account,datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))
                break
            else:
                now = datetime.now()
                seconds = int((exchange_start_datetime - now).seconds)
                millisecond = int((exchange_start_datetime - now).seconds * 1000 +
                                  (exchange_start_datetime - now).microseconds / 1000)
                println('{}, 距离兑换开始还有{}秒!'.format(self.account, seconds), millisecond)
                timeout = millisecond / 1000
                println('{}, 当前时间小于兑换时间, 等待{}秒!'.format(self.account, timeout))
                await asyncio.sleep(timeout)
        # 记录火爆次数
        errBizCodeCount = 0
        success_count = 0
        stack_over = 0
        run_count = 0

        while True:
            run_count += 1
            println(f'{self.account}, 开始第{run_count}次兑换...')
            data = await self.obtain_prize(session)
            try:
                if data['bizCode'] == 0:
                    self.buy_limit -= 1
                    success_count += 1
                    self.total_blue_coin -= self.cost
                    println(f'{self.account},兑换成功: {data}')
                elif data['bizCode'] == 400:
                    errBizCodeCount += 1
                    println(f'{self.account}, 兑换错误: {data["bizMsg"]}')
                elif data['bizCode'] == 505:
                    stack_over += 1
                    println(f'{self.account}, 奖品库存不足!({data["bizMsg"]})')
                else:
                    errBizCodeCount += 1
                    println(f'{self.account}, 兑换商品出错!({data["bizMsg"]})')
                    println(f'{self.account}, data = {data}')
            except Exception as e:
                errBizCodeCount += 1
                println(f'{self.account}, 兑换异常!{e.args}, {data}')
            
            if self.buy_limit <= 0 or stack_over >= 10 or errBizCodeCount >= 20:
                    break
            if self.total_blue_coin < self.cost:
                println(f'{self.account},你没有足够的蓝币兑换!(需要: {self.cost},拥有: {self.totalBlue})')
                break

        println(f'{self.account}, 总共尝试兑换{run_count}次, 成功{success_count}次, 异常{errBizCodeCount}次!')
        if success_count > 0:
            exchange_success_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            self.message = f'【活动名称】东东超市蓝币兑换\n【京东账号】{self.account}\n【兑换奖品】{JD_SUPERMARKET_EXCHANGE}\n【兑换状态】成功{success_count}次\n【兑换时间】{exchange_success_datetime}\n'

    @logger.catch
    async def run(self):
        if not JD_SUPERMARKET_EXCHANGE:
            println(f'{self.account}, 你未设置兑换商品,退出执行.')
            return
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            home_data = await self.get_home_data(session)
            if not home_data:
                println('{}, 由于无法获取首页数据, 退出程序...'.format(self.account))
                return
            # self.totalGold = home_data.get('totalGold',0)
            self.total_blue_coin = home_data.get('totalBlue',0)
            good_name = ''
            if JD_SUPERMARKET_EXCHANGE == 20:
                good_name = '万能的京豆'
                self.buy_limit = 20
            elif JD_SUPERMARKET_EXCHANGE == 1000:
                good_name = '超值京豆包'
            else:
                good_name = JD_SUPERMARKET_EXCHANGE
            await self.query_price(session,good_name)
            if not self.areaId:
                return
            if self.total_blue_coin < self.cost:
                println(f'{self.account},你没有足够的蓝币兑换!(需要: {self.cost},拥有: {self.totalBlue})')
                return
            await self.do_exchange(session)



if __name__ == '__main__':
    from config import JD_SUPERMARKET_EXCHANGE
    # from config import JD_COOKIES
    # app = JdBlueCoin(**JD_COOKIES[0])
    # asyncio.run(app.run())
    from utils.process import process_start
    process_start(JdSupermarketExchange, '东东超市蓝币兑换')
