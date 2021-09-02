#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/25 1:18 下午
# @File    : jr_pet_pig.py
# @Project : jd_scripts
# @Cron    : 23 0-23/8 * * *
# @Desc    : 京东金融APP->我的->养猪猪
import asyncio
import aiohttp
import json
import time
from urllib.parse import quote, urlencode
from furl import furl
from utils.process import process_start
from utils.console import println
from utils.jd_init import jd_init
from config import USER_AGENT


@jd_init
class JrPetPig:
    """
    养猪猪
    """
    # 活动地址
    host = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/'

    headers = {
        'accept': 'application/json',
        'origin': 'https://u.jr.jd.com',
        'user-agent': USER_AGENT,
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'referer': 'https://u.jr.jd.com/uc-fe-wxgrowing/cloudpig/index/'
    }

    async def request(self, session, function_id, body=None, method='POST'):
        """
        请求数据
        :param method:
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        try:
            await asyncio.sleep(1)
            url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/{}/?_={}&'.format(function_id, int(time.time() * 1000))
            if not body:
                body = {}
            params = {
                'reqData': json.dumps(body)
            }
            url += urlencode(params)

            println(url)
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)

            text = await response.text()
            data = json.loads(text)
            return data

        except Exception as e:
            println('{}, 请求服务器数据失败, {}'.format(self.account, e.args))
            return None

    async def login(self, session):
        """
        :return:
        """
        try:
            data = await self.request(session, 'pigPetLogin', {"source": 2, "channelLV": "juheye",
                                                               "riskDeviceParam": '{}'})

            if data['resultCode'] != 0 or data['resultData']['resultCode'] != 0:
                println('{}, 登录失败, {}'.format(self.account, data))
                return False
            if 'hasPig' not in data['resultData']['resultData'] or not data['resultData']['resultData']['hasPig']:
                println('{}, 未开启养猪猪活动, 请前往京东金融APP开启!'.format(self.account))
                return False
            return True
        except Exception as e:
            println('{}, 登录失败, {}'.format(self.account, e.args))
            return False

    async def sign(self, session):
        """
        签到
        :param session:
        :return:
        """
        try:
            data = await self.request(session, 'pigPetSignIndex',
                                      {"source": 0, "channelLV": "", "riskDeviceParam": "{}"})

            sign_list = data['resultData']['resultData']['signList']
            today = data['resultData']['resultData']['today']
            for sign_item in sign_list:
                if sign_item['no'] != today:
                    continue

                # 找到今天的签到数据
                if sign_item['status'] != 0:
                    println('{}, 今日已签到!'.format(self.account))
                    break

                sign_url = self.host + 'pigPetSignOne?_={}'.format(int(time.time() * 1000))
                body = 'reqData={}'.format(quote(json.dumps({"source": 0, "no": sign_item['no'],
                                                             "channelLV": "", "riskDeviceParam": "{}"})))
                response = await session.post(url=sign_url, data=body)
                text = await response.text()
                data = json.loads(text)
                if data['resultCode'] == 0:
                    println('{}, 签到成功!'.format(self.account))
                else:
                    println('{}, 签到失败, {}'.format(self.account, data['resultMsg']))
                break

        except Exception as e:
            println('{}, 签到失败, 异常:{}'.format(self.account, e.args))

    async def open_box(self, session):
        """
        开宝箱
        :param session:
        :return:
        """
        try:
            data = await self.request(session, 'pigPetOpenBox', {
                "source": 0, "channelLV": "yqs", "riskDeviceParam": "{}", "no": 5,
                "category": "1001", "t": int(time.time() * 1000)
            })
            if data['resultData']['resultCode'] != 0:
                println('{}, {}!'.format(self.account, data['resultData']['resultMsg']))
                return
            if 'award' not in data['resultData']['resultData']:
                return
            content = data['resultData']['resultData']['award']['content']
            count = data['resultData']['resultData']['award']['count']
            println('{}, 开宝箱获得:{}, 数量:{}'.format(self.account, content, count))
            await self.open_box(session)
        except Exception as e:
            println('{}, 开宝箱失败, {}'.format(self.account, e.args))

    async def lottery(self, session):
        """
        抽奖
        :param session:
        :return:
        """
        try:
            data = await self.request(session, 'pigPetLotteryIndex', {
                "source": 0,
                "channelLV": "juheye",
                "riskDeviceParam": "{}"
            })
            lottery_count = data['resultData']['resultData']['currentCount']
            if lottery_count < 1:
                println('{}, 暂无抽奖次数!'.format(self.account))
                return

            for i in range(lottery_count):
                data = await self.request(session, 'pigPetLotteryPlay', {
                    "source": 0,
                    "channelLV": "juheye",
                    "riskDeviceParam": "{}",
                    "t": int(time.time() * 1000),
                    "type": 0,
                })
                if data['resultData']['resultCode'] == 0:
                    println('{}, 抽奖成功!'.format(self.account))
                else:
                    println('{}, 抽奖失败!'.format(self.account))
                await asyncio.sleep(1)

        except Exception as e:
            println('{}, 抽奖失败, {}'.format(self.account, e.args))

    async def do_mission(self, session, mission):
        """
        做任务
        :return:
        """
        try:
            mission_id = mission['mid'].replace('MC', '')
            res = await self.request_mission(session, 'queryMissionReceiveAfterStatus',
                                             {"missionId": mission_id})
            if not res or res['resultCode'] != 0 or res['resultData']['code'] != '0000':
                return False

            # 任务URL带有readTime的表示需要等待N秒, 没有则等待一秒, 防止频繁访问出错
            t = int(furl(mission['url']).args.get('readTime', 0))

            if t == 0:  # 非浏览任务做不了
                return False

            println('{}, 正在做任务:{}, 需要等待{}S.'.format(self.account, mission['missionName'], t))

            await asyncio.sleep(int(t))

            res = await self.request_mission(session, 'finishReadMission', {"missionId": str(mission_id),
                                                                            "readTime": t})
            if not res or res['resultCode'] != 0 or res['resultData']['code'] != '0000':
                return False
            return True

        except Exception as e:
            println(e.args)
            return False

    async def receive_or_finish_mission(self, session, mission):
        """
        领取任务或完成任务!
        :param mission:
        :param session:
        :return:
        """
        await asyncio.sleep(1)
        try:
            mission_url = self.host + 'pigPetDoMission?_='.format(int(time.time() * 1000))
            body = 'reqData={}'.format(quote(json.dumps({
                "source": 0,
                "channelLV": "",
                "riskDeviceParam": "{}",
                "mid": mission['mid']
            })))
            response = await session.post(url=mission_url, data=body)
            text = await response.text()
            data = json.loads(text)
            return data['resultData']
        except Exception as e:
            println(e.args)

    async def request_mission(self, session, function_id, body):
        """
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        try:
            url = 'https://ms.jr.jd.com/gw/generic/mission/h5/m/{}?reqData={}'.format(function_id,
                                                                                      quote(json.dumps(body)))
            response = await session.get(url=url)
            text = await response.text()
            await asyncio.sleep(1)
            data = json.loads(text)
            return data
        except Exception as e:
            println("{}, 访问服务器异常, 信息:{}".format(self.account, e.args))

    async def missions(self, session):
        """
        做任务
        :param session:
        :return:
        """
        url = self.host + 'pigPetMissionList?_={}'.format(int(time.time() * 1000))
        body = 'reqData={}'.format(quote(json.dumps({
            "source": 0,
            "channelLV": "",
            "riskDeviceParam": "{}"
        })))
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            mission_list = data['resultData']['resultData']['missions']
            for mission in mission_list:
                if mission['status'] == 5:
                    println('{}, 任务:{}, 今日已完成!'.format(self.account, mission['missionName']))
                    continue
                if mission['status'] == 4:
                    data = await self.receive_or_finish_mission(session, mission)
                    if data['resultCode'] == 0:
                        println('{}, 成功领取任务:{}的奖励!'.format(self.account, mission['missionName']))
                    else:
                        println('{}, 领取任务:{}奖励失败!'.format(self.account, mission['missionName']))

                if mission['status'] == 3:
                    await self.receive_or_finish_mission(session, mission)
                    await asyncio.sleep(0.5)
                    success = await self.do_mission(session, mission)
                    if not success:
                        continue
                    await asyncio.sleep(1)
                    data = await self.receive_or_finish_mission(session, mission)
                    await asyncio.sleep(0.5)
                    if data['resultCode'] == 0:
                        println('{}, 成功领取任务:{}的奖励!'.format(self.account, mission['missionName']))
                    else:
                        println('{}, 领取任务:{}奖励失败!'.format(self.account, mission['missionName']))

        except Exception as e:
            println("{}, 获取任务列表失败!".format(e.args))

    async def add_food(self, session):
        """
        喂猪
        :return:
        """
        try:
            data = await self.request(session, 'pigPetUserBag',
                                      {"source": 0, "channelLV": "yqs", "riskDeviceParam": "{}",
                                       "t": int(time.time() * 1000),
                                       "skuId": "1001003004",
                                       "category": "1001"})
            if data['resultCode'] != 0 or data['resultData']['resultCode'] != 0:
                println("{}, 查询背包信息失败, 无法喂猪!".format(self.account))
                return
            goods_list = data['resultData']['resultData']['goods']

            for goods in goods_list:
                if goods['count'] < 20:  # 大于20个才能喂猪
                    continue
                times = int(goods['count'] / 20)  # 可喂猪次数

                for i in range(times):
                    data = await self.request(session, 'pigPetAddFood', {
                        "source": 0,
                        "channelLV": "yqs",
                        "riskDeviceParam": "{}",
                        "skuId": str(goods['sku']),
                        "category": "1001",
                    })
                    if data['resultCode'] == 0 and data['resultData']['resultCode'] == 0:
                        println('{}, 成功投喂20个{}'.format(self.account, goods['goodsName']))
                        println('{}, 等待10s后进行下一次喂猪!'.format(self.account))
                        await asyncio.sleep(10)
                    else:
                        println('{}, 投喂20个{}失败!'.format(self.account, goods['goodsName']))
            println('{}, 食物已消耗完, 结束喂猪!'.format(self.account))
        except Exception as e:
            println('喂猪失败!异常:{}'.format(e.args))

    async def run(self):
        """
        入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            data = await self.request(session, 'pigPetLogin', {
                "source": 2,
                "channelLV": "juheye",
                "riskDeviceParam": "{}",
            })
            return
            is_login = await self.login(session)
            if not is_login:
                println('{},登录失败, 退出程序...'.format(self.account))
                return
            await self.sign(session)
            await self.missions(session)
            await self.open_box(session)
            await self.lottery(session)
            await self.add_food(session)
            #await self.notify(session)

    async def notify(self, session):
        """
        通知
        :return:
        """
        try:
            await asyncio.sleep(1)  # 避免查询失败
            data = await self.request(session, 'pigPetLogin', {
                "source": 2,
                "channelLV": "juheye",
                "riskDeviceParam": "{}",
            })
            curr_level_count = data['resultData']['resultData']['cote']['pig']['currLevelCount']  # 当前等级需要喂养的次数
            curr_count = data['resultData']['resultData']['cote']['pig']['currCount']  # 当前等级已喂猪的次数
            curr_level = data['resultData']['resultData']['cote']['pig']['curLevel']
            curr_level_message = '成年期' if curr_level == 3 else '哺乳期'
            pig_id = data['resultData']['resultData']['cote']['pig']['pigId']

            data = await self.request(session, 'pigPetMyWish1', {
                "pigId": pig_id,
                "channelLV": "",
                "source": 0,
                "riskDeviceParam": "{}"})
            award_name = data['resultData']['resultData']['award']['name']
            award_tips = data['resultData']['resultData']['award']['content']
            message = '\n【活动名称】{}\n【用户ID】{}\n【奖品名称】{}\n【完成进度】{}\n【小提示】{}'.format(
                '京东金融养猪猪', self.account, award_name,
                '{}:{}/{}'.format(curr_level_message, curr_count, curr_level_count), award_tips
            )
            self.message = message
        except Exception as e:
            println(e.args)


if __name__ == '__main__':
    process_start(JrPetPig, '养猪猪')
