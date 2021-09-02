#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/18 3:42 下午
# @File    : jd_notification.py
# @Project : jd_scripts
# @Cron    : 30 9,19 * * *
# @Desc    : 京东活动通知
import asyncio
import json
import time

import ujson
from urllib.parse import quote
import aiohttp
import moment

from config import USER_AGENT
from utils.jd_init import jd_init
from utils.console import println
from utils.logger import logger


@jd_init
class JdNotification:
    """
    统一消息通知
    """
    headers = {
        'user-agent': USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
        'host': 'api.m.jd.com'
    }

    @logger.catch
    async def request(self, url, **kwargs):
        """
        请求数据
        :param url:
        :return:
        """
        try:
            body = kwargs.get('body', '')
            method = kwargs.get('method', 'GET')
            json_data = kwargs.get('json_data', '')
            headers = kwargs.get('headers', self.headers)
            async with aiohttp.ClientSession(cookies=self.cookies, headers=headers,
                                             json_serialize=ujson.dumps) as session:
                if method == 'GET':
                    request_func = session.get
                else:
                    request_func = session.post

                if json_data:
                    response = await request_func(url=url, json=json_data)
                else:
                    response = await request_func(url=url, data=body)

                text = await response.text()

                data = json.loads(text)

                return data

        except Exception as e:
            println('{}, 请求服务器失败, {}, {}'.format(self.account, e.args, url))
            return dict()

    @logger.catch
    async def get_bean_msg(self):
        """
        获取收入/支出京豆
        :return:
        """
        headers = {
            'Host': 'api.m.jd.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': USER_AGENT,
            'Referer': 'https://wqs.jd.com/promote/201801/bean/mybean.html'
        }

        url = 'https://api.m.jd.com/client.action?functionId=getJingBeanBalanceDetail'
        total_bean = 0  # 京豆总数
        today_income = 0  # 今日收入
        today_used = 0  # 今日支出
        yesterday_income = 0  # 昨日收入
        yesterday_used = 0  # 昨日支出
        yesterday = moment.date(moment.now().sub('days', 1)).zero  # 昨天
        today = moment.date(moment.now()).zero  # 今天

        finished = False

        for page in range(1, 10):
            headers['Referer'] = 'https://api.m.jd.com/client.action?functionId=getJingBeanBalanceDetail'
            body = 'body={}&appid=ld'.format(quote(json.dumps({"pageSize": "20", "page": str(page)})))
            res = await self.request(url, body=body, method='POST', headers=headers)
            if not res.get('detailList', []):
                break
            item_list = res.get('detailList')

            for item in item_list:
                day = moment.date(item['date'], '%H:%M:%S').zero
                amount = int(item['amount'])
                if '退还京豆' in item.get('eventMassage', ''):
                    continue
                if day.diff(yesterday).days == 0:
                    if amount > 0:  # 收入
                        yesterday_income += amount
                    else:  # 支出
                        yesterday_used += -amount

                elif day.diff(yesterday).days >= 1:  # 昨天之前的日期跳过
                    finished = True
                    break

                if day.diff(today).days == 0:
                    if amount > 0:
                        today_income += amount
                    else:
                        today_used = -amount
            if finished:
                break
            await asyncio.sleep(0.2)

        url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
        headers['Host'] = 'me-api.jd.com'
        headers['Referer'] = 'https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&'
        data = await self.request(url, headers=headers, method='GET')
        if data:
            total_bean = data['data']['assetInfo']['beanNum']

        message = f'【当前京豆总数】{total_bean} \n【今日收入京豆】{today_income}\n' \
                  f'【今日支出京豆】{today_used}\n【昨日收入京豆】{yesterday_income}\n【昨日支出京豆】{yesterday_used}'

        return message

    @logger.catch
    async def get_jd_farm_msg(self):
        """
        获取东东农场信息
        :return:
        """
        headers = {
            'user-agent': USER_AGENT,
            'x-requested-with': 'com.jingdong.app.mall',
            'sec-fetch-mode': 'cors',
            'origin': 'https://carry.m.jd.com',
            'sec-fetch-site': 'same-site',
            'referer': 'https://carry.m.jd.com/babelDiy/Zeus/3KSjXqQabiTuD1cJ28QskrpWoBKT/index.html'
        }
        url = 'https://api.m.jd.com/client.action?functionId=initForFarm&body=%7B%22babelChannel%22%3A%22121%22%2C' \
              '%22lng%22%3A%22113.383803%22%2C%22lat%22%3A%2223.102671%22%2C%22sid%22%3A' \
              '%228e51862fd39a3498a6de0093dc06539w%22%2C%22un_area%22%3A%2219_1601_36953_50397%22%2C%22version%22' \
              '%3A14%2C%22channel%22%3A1%7D&appid=wh5'
        res = await self.request(url=url, headers=headers)

        data = res.get('farmUserPro', dict())

        award_name = data.get('name', '查询失败')
        award_percentage = round(data.get('treeEnergy', 0.0) / data.get('treeTotalEnergy', 0.1) * 100, 2)

        message = f'【东东农场】{award_name}, 进度:{award_percentage}%'

        return message

    @logger.catch
    async def get_jd_earn_msg(self):
        """
        获取京东赚赚信息

        :return:
        """
        headers = {
            'referer': 'https://servicewechat.com/wx8830763b00c18ac3/96/page-frame.html',
            'wqreferer': 'http://wq.jd.com/wxapp/pages/hd-interaction/task/index',
            'user-agent': USER_AGENT.replace('jdapp;', ''),
            'content-type': 'application/json'
        }

        url = 'https://api.m.jd.com/client.action?functionId=interactTaskIndex&body=%7B%27mpVersion%27%3A+%273.4.0%27' \
              '%7D&client=wh5&clientVersion=9.1.0'

        res = await self.request(url, headers=headers)

        amount = round(int(res.get('data', dict()).get('totalNum', 0)) / 10000, 2)

        msg = f'【京东赚赚】可提现:{amount}元'

        return msg

    @logger.catch
    async def get_jd_sec_coin_msg(self):
        """
        获取秒秒比信息
        :return:
        """
        headers = {
            'user-agent': USER_AGENT,
            'content-type': 'application/x-www-form-urlencoded',
            'referer': 'https://h5.m.jd.com/babelDiy/Zeus/2NUvze9e1uWf4amBhe1AV6ynmSuH/index.html',
            'origin': 'https://h5.m.jd.com',
        }

        url = 'https://api.m.jd.com/client.action?clientVersion=10.1.2&client=wh5&osVersion=&area=&networkType=wifi' \
              '&functionId=homePageV2&body=%7B%7D&appid=SecKill2020'

        res = await self.request(url, headers=headers)

        point = res.get('result', dict()).get('assignment', dict()).get('assignmentPoints', 0.0)

        amount = point / 1000

        msg = f'【秒秒币】 数量:{point}, 可提现:{amount}元'

        return msg

    @logger.catch
    async def get_jd_supermarket_msg(self):
        """
        获取东东超市蓝币信息
        :return:
        """
        headers = {
            'origin': 'https://jdsupermarket.jd.com',
            'user-agent': USER_AGENT,
            'referer': 'https://jdsupermarket.jd.com/game/?tt={}'.format(int(time.time() * 1000)),
            'content-type': 'application/x-www-form-urlencoded',
        }

        url = 'https://api.m.jd.com/api?functionId=smtg_newHome&appid=jdsupermarket&clientVersion=8.0.0&client=m&t' \
              '=1631957189&body=%7B%22channel%22%3A+%221%22%7D'
        res = await self.request(url, headers=headers)

        blue_count = res.get('data', dict()).get('result', dict()).get('totalBlue', 0)

        msg = f'【东东超市】蓝币数量:{blue_count}'

        return msg

    @logger.catch
    async def get_jd_factory_msg(self):
        """
        获取东东工厂信息
        :return:
        """
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://h5.m.jd.com',
        }

        url = 'https://api.m.jd.com/client.action/?functionId=jdfactory_getHomeData&body=%7B%7D&client=wh5' \
              '&clientVersion=1.0.0'
        res = await self.request(url, headers=headers)

        data = res.get('data', dict()).get('result', dict()).get('factoryInfo', dict())

        name = data.get('name', '无')
        need_amount = int(data.get('totalScore', '0'))
        used_amount = int(data.get('useScore', '0'))
        remain_amount = int(data.get('remainScore', '0'))

        msg = f'【东东工厂】奖品:{name}, 投入电量:{used_amount}/{need_amount}, 剩余电量:{remain_amount}'

        return msg

    @logger.catch
    async def get_jd_car_msg(self):
        """
        获取京东汽车信息
        :return:
        """
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-cn",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "car-member.jd.com",
            "Referer": "https://h5.m.jd.com/babelDiy/Zeus/44bjzCpzH9GpspWeBzYSqBA7jEtP/index.html",
        }

        url = 'https://car-member.jd.com/api/v1/user/point?timestamp={}'.format(int(time.time()*1000))

        res = await self.request(url, headers=headers, method='GET')

        data = res.get('data', dict())

        if not data:
            data = dict()

        point = data.get('remainPoint', 0)

        msg = f'【京东汽车】积分:{point}'

        return msg

    @logger.catch
    async def get_jd_cash_msg(self):
        """
        获取领现金信息
        :return:
        """
        headers = {
            'Accept-Language': 'zh-cn',
            'Accept-Encoding': 'gzip, deflate, br',
            'Host': 'api.m.jd.com',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Referer': 'https://wq.jd.com/wxapp/pages/hd-interaction/index/index',
        }
        url = 'https://api.m.jd.com/client.action?functionId=cash_homePage&clientVersion=10.1.2&build=89743&client' \
              '=android&openudid=a27b83d3d1dba1cc&uuid=a27b83d3d1dba1cc&aid=a27b83d3d1dba1cc&networkType=wifi' \
              '&harmonyOs=0&st=1631958646482&sign=58ebf3d09bb5d97b87d95e49e419a19b&sv=110&body=%7B%7D&'
        res = await self.request(url, headers=headers)

        total_amount = res.get('data', dict()).get('result', dict()).get('totalMoney', 0.0)

        msg = f'【签到领现金】当前金额:{total_amount}元'

        return msg

    @logger.catch
    async def get_jd_cut_pet_msg(self):
        """
        获取东东萌宠信息
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=initPetTown&body=%7B%22version%22%3A%202%2C%20%22channel' \
              '%22%3A%20%22app%22%7D&appid=wh5&loginWQBiz=pet-town&clientVersion=9.0.4'
        res = await self.request(url)
        if res.get('code') != '0':
            return '【东东萌宠】查询失败'

        data = res.get('result')

        pet_status = data.get('petStatus')

        if pet_status == 5:
            goods_name = data.get('goodsInfo', dict()).get('goodsName', '未知')
            msg = f'【东东萌宠】奖品:{goods_name}, 已可兑换!'
            return msg
        elif pet_status == 6:
            return '【东东萌宠】暂未领取新奖品'

        goods_name = data.get('goodsInfo', dict()).get('goodsName', '未知')
        medal_num = data.get('medalNum', 0)
        exchange_num = data.get('goodsInfo', dict()).get('exchangeMedalNum', 0)
        medal_percent = data.get('medalPercent', 0.0)

        msg = '【东东萌宠】奖品:{}, 勋章: {}/{}, 第{}块勋章进度:{}%'.format(goods_name,
                                                            medal_num, exchange_num, medal_num + 1, medal_percent)

        return msg

    @logger.catch
    async def get_jd_health_msg(self):
        """
        获取东东健康社区信息
        """
        headers = {
            'user-agent': USER_AGENT,
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://h5.m.jd.com',
            'referer': 'https://h5.m.jd.com/',
        }
        url = 'https://api.m.jd.com/?functionId=jdhealth_getHomeData&client=wh5&body=%7B%7D&clientVersion=1.0.0&uuid='

        res = await self.request(url, headers=headers)

        user_score = res.get('data', dict()).get('result', dict()).get('userScore', 0)

        msg = f'【东东健康社区】能量:{user_score}'

        return msg

    @logger.catch
    async def get_jd_planting_bean_msg(self):
        """
        获取种豆得豆信息
        """
        headers = {
            "Host": "api.m.jd.com",
            "Accept": "*/*",
            "Connection": "keep-alive",
            "User-Agent": USER_AGENT,
            "Accept-Language": "zh-Hans-CN;q=1,en-CN;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        url = 'https://api.m.jd.com/client.action?functionId=plantBeanIndex&body=%7B%22version%22%3A%20%229.2.4.0%22' \
              '%2C%20%22monitor_source%22%3A%20%22plant_app_plant_index%22%2C%20%22monitor_refer%22%3A%20%22%22%7D' \
              '&appid=ld&client=apple&area=19_1601_50258_51885&build=167490&clientVersion=9.3.2'

        res = await self.request(url, headers=headers)

        round_list = res.get('data', dict()).get('roundList', list())
        growth = 0
        last_award_beans = 0
        for item in round_list:
            if '本期' in item['dateDesc']:
                growth = item['growth']
            if '上期' in item['dateDesc']:
                last_award_beans = item.get('awardBeans', 0)

        return f'【种豆得豆】本期成长值:{growth}, 上期兑换京豆:{last_award_beans}'

    async def get_jr_daily_take_goose_msg(self):
        """
        获取天天提额信息
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
        url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/queryGoldExchange?reqData=%7B%7D'
        res = await self.request(url, headers=headers, method='POST')

        point = res.get('resultData', dict()).get('data', dict()).get('goldTotal', 0)

        return f'【天天提鹅】积分:{point}'

    @logger.catch
    async def get_jr_money_tree_msg(self):
        """
        获取金果摇钱树信息
        """
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Origin': 'https://uua.jr.jd.com',
            'Referer': 'https://uua.jr.jd.com/',
            'User-Agent': USER_AGENT,
        }
        url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/login?_=1632118021632&reqData=%7B%22sharePin%22%3A%20%22%22%2C' \
              '%20%22shareType%22%3A%201%2C%20%22channelLV%22%3A%20%22%22%2C%20%22source%22%3A%200%2C%20' \
              '%22riskDeviceParam%22%3A%20%22%7B%7D%22%7D'
        res = await self.request(url, method='POST', headers=headers)

        fruit_amount = res.get('resultData', dict()).get('data', dict()).get('treeInfo', dict()).get('fruit', 0)

        msg = f'【金果摇钱树】金果数量:{fruit_amount}'

        return msg

    @logger.catch
    async def get_jr_pet_pig_msg(self):
        """
        获取金融养猪信息
        """
        headers = {
            'accept': 'application/json',
            'origin': 'https://u.jr.jd.com',
            'user-agent': USER_AGENT,
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'referer': 'https://u.jr.jd.com/uc-fe-wxgrowing/cloudpig/index/'
        }

        url = f'https://ms.jr.jd.com/gw/generic/uc/h5/m/pigPetLogin/?_={int(time.time())}&reqData=%7B%22source%22%3A' \
              f'+2%2C+%22channelLV%22%3A+%22juheye%22%2C+%22riskDeviceParam%22%3A+%22%7B%7D%22%7D'

        try:
            res = await self.request(url)
            data = res['resultData']['resultData']
            if not data.get('cote', dict()).get('pig', None):
                return f'【金融养猪】未开启活动'
            curr_level_count = data['cote']['pig']['currLevelCount']  # 当前等级需要喂养的次数
            curr_count = data['cote']['pig']['currCount']  # 当前等级已喂猪的次数
            curr_level = data['cote']['pig']['curLevel']
            curr_level_message = '成年期' if curr_level == 3 else '哺乳期'
            msg = f'【金融养猪】{curr_level_message}:{curr_count}/{curr_level_count}'
            return msg
        except Exception as e:
            println(e.args)
            return ''

    @logger.catch
    async def notify(self):
        """
        京东资产变动通知
        :return:
        """
        title = '【京东账号】{}'.format(self.account)
        jd_farm_msg = await self.get_jd_farm_msg()
        jd_cash_msg = await self.get_jd_cash_msg()
        jd_earn_msg = await self.get_jd_earn_msg()
        jd_car_msg = await self.get_jd_car_msg()
        jd_factory_msg = await self.get_jd_factory_msg()
        jd_supermarket_msg = await self.get_jd_supermarket_msg()
        jd_sec_coin_msg = await self.get_jd_sec_coin_msg()
        jd_cut_pet_msg = await self.get_jd_cut_pet_msg()
        bean_msg = await self.get_bean_msg()
        jd_health_msg = await self.get_jd_health_msg()
        jd_planting_bean_msg = await self.get_jd_planting_bean_msg()
        jr_daily_take_goose_msg = await self.get_jr_daily_take_goose_msg()
        jr_money_tree_msg = await self.get_jr_money_tree_msg()
        jr_pet_pig_msg = await self.get_jr_pet_pig_msg()
        tail = '-' * 60 + '\n\n'

        self.message = '\n'.join([i for i in [
            title,
            bean_msg,
            jd_earn_msg,
            jd_cash_msg,
            jd_car_msg,
            jd_farm_msg,
            jd_factory_msg,
            jd_supermarket_msg,
            jd_sec_coin_msg,
            jd_cut_pet_msg,
            jd_health_msg,
            jd_planting_bean_msg,
            jr_daily_take_goose_msg,
            jr_money_tree_msg,
            jr_pet_pig_msg,
            tail
        ] if i])

    async def run(self):
        await self.notify()


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdNotification, '消息通知')
