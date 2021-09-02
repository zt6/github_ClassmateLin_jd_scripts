#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/21 21:47
# @File    : jd_planting_bean.py
# @Project : jd_scripts
# @Cron    : 10 3,15 * * *
# @Desc    : 京东APP->我的->签到领豆->种豆得豆

import asyncio
import aiohttp
import re
import json
import moment
from functools import wraps
from urllib.parse import quote

from furl import furl
from utils.console import println
from utils.logger import logger
from utils.process import process_start, get_code_list
from utils.jd_init import jd_init

from db.model import Code
from config import USER_AGENT

# 种豆得豆助力码
CODE_PLANTING_BEAN = 'planting_bean'


def println_task(func=None):
    """
    输出任务
    :param func:
    :return:
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        task = args[-1]
        if task['isFinished'] or (int(task['totalNum']) - int(task['gainedNum']) == 0):  # 今天已经完成任务了！
            println('{}, 任务:{}, 今日已完成过或已达到上限, 不需要重复执行！'.format(task['account'], task['taskName']))
            return

        if task['taskType'] == 8:  # 评价商品任务
            println('{}, 任务:{}, 请手动到APP中完成！'.format(task['account'], task['taskName']))
            return

        println('{}, 开始做{}任务!'.format(task['account'], task['taskName']))
        res = await func(*args, **kwargs)
        println('{}, 已完成{}任务!'.format(task['account'], task['taskName']))
        return res

    return wrapper


@jd_init
class JdPlantingBean:
    """
    种豆得豆
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

    cur_round_id = None  # 本期活动id
    prev_round_id = None  # 上期活动id
    next_round_id = None  # 下期活动ID
    cur_round_list = None
    prev_round_list = None
    task_list = None  # 任务列表
    nickname = None  # 京东昵称
    share_code = None
    
    async def post(self, session, function_id, params=None):
        """
        :param session:
        :param function_id:
        :param params:
        :return:
        """
        if params is None:
            params = {}
        params['version'] = '9.2.4.0'
        params['monitor_source'] = 'plant_app_plant_index'
        params['monitor_refer'] = ''

        url = 'https://api.m.jd.com/client.action'

        body = f'functionId={function_id}&body={quote(json.dumps(params))}&appid=ld' \
               f'&client=apple&area=19_1601_50258_51885&build=167490&clientVersion=9.3.2'

        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            await asyncio.sleep(1)
            data = json.loads(text)
            return data

        except Exception as e:
            logger.error('{}, 种豆得豆访问服务器失败:[function_id={}], 错误信息:{}'.format(self.account, function_id, e.args))

    async def get(self, session, function_id, body=None, wait_time=1):
        """
        :param wait_time:
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        if body is None:
            body = {}

        try:
            body["version"] = "9.2.4.0"
            body["monitor_source"] = "plant_app_plant_index"
            body["monitor_refer"] = ""

            url = f'https://api.m.jd.com/client.action?functionId={function_id}&body={quote(json.dumps(body))}&appid=ld'
            response = await session.get(url=url)
            text = await response.text()
            data = json.loads(text)
            if wait_time > 0:
                await asyncio.sleep(1)
            return data

        except Exception as e:
            logger.error('{}, 种豆得豆访问服务器失败:[function_id={}], 错误信息:{}'.format(self.account, function_id, e.args))

    async def planting_bean_index(self, session):
        """
        :return:
        """
        data = await self.post(session=session, function_id='plantBeanIndex')

        if not data or data['code'] != '0' or 'errorMessage' in data:
            println('{},访问种豆得豆首页失败, 退出程序！错误原因:{}'.format(self.account, data))
            return False
        data = data['data']

        round_list = data['roundList']
        cur_idx = 2
        prev_idx = 1
        prev_start_date = moment.date('01-01')
        for i in range(len(round_list)):
            rnd = round_list[i]
            if '本期' in rnd['dateDesc']:
                cur_idx = i
                break
            elif '上期' in rnd['dateDesc']:
                temp = re.search('-(\d+月\d+)日', rnd['dateDesc']).group(1).replace('月', '-')
                prev_date = moment.date(temp)
                if prev_date > prev_start_date:
                    prev_start_date = prev_date
                    prev_idx = i

        self.cur_round_id = round_list[cur_idx]['roundId']
        self.task_list = data['taskList']
        self.cur_round_list = round_list[cur_idx]
        self.prev_round_list = round_list[prev_idx]
        self.message = '\n【活动名称】种豆得豆\n'
        self.message += f"【京东昵称】:{data['plantUserInfo']['plantNickName']}\n"
        self.message += f'【上期时间】:{round_list[prev_idx]["dateDesc"].replace("上期 ", "")}\n'
        self.message += f'【上期成长值】:{round_list[prev_idx]["growth"]}\n'
        return True

    async def receive_nutrient(self, session):
        """
        收取营养液
        :param session:
        :return:
        """
        println('{}, 开始收取营养液!'.format(self.account))
        data = await self.post(session, 'receiveNutrients',
                               {"roundId": self.cur_round_id, "monitor_refer": "plant_receiveNutrients"})
        println('{}, 完成收取营养液, {}'.format(self.account, data))

    @println_task
    async def receive_nutrient_task(self, session, task):
        """
        :param session:
        :param task:
        :return:
        """
        params = {
            "monitor_refer": "plant_receiveNutrientsTask",
            "awardType": str(task['taskType'])
        }
        data = await self.get(session, 'receiveNutrientsTask', params)
        println('{}, 收取营养液:{}'.format(self.account, data))

    @println_task
    async def visit_shop_task(self, session, task):
        """
        浏览店铺任务
        :param session:
        :param task:
        :return:
        """
        shop_data = await self.get(session, 'shopTaskList', {"monitor_refer": "plant_receiveNutrients"})
        if shop_data['code'] != '0':
            println('{}, 获取{}任务失败!'.format(self.account, task['taskName']))

        shop_list = shop_data['data']['goodShopList'] + shop_data['data']['moreShopList']
        for shop in shop_list:
            body = {
                "monitor_refer": "plant_shopNutrientsTask",
                "shopId": shop["shopId"],
                "shopTaskId": shop["shopTaskId"]
            }
            data = await self.get(session, 'shopNutrientsTask', body)
            if data['code'] == '0' and 'data' in data:
                println('{}, 浏览店铺结果:{}'.format(self.account, data['data']))
            else:
                println('{}, 浏览店铺结果:{}'.format(self.account, data['errorMessage']))
            await asyncio.sleep(1)

    @println_task
    async def pick_goods_task(self, session, task):
        """
        挑选商品任务
        :return:
        """
        data = await self.get(session, 'productTaskList', {"monitor_refer": "plant_productTaskList"})

        for products in data['data']['productInfoList']:
            for product in products:
                body = {
                    "monitor_refer": "plant_productNutrientsTask",
                    "productTaskId": product['productTaskId'],
                    "skuId": product['skuId']
                }
                res = await self.get(session, 'productNutrientsTask', body)
                if 'errorCode' in res:
                    println('{}, {}'.format(self.account, res['errorMessage']))
                else:
                    println('{}, {}'.format(self.account, res))

                await asyncio.sleep(1)

    @println_task
    async def focus_channel_task(self, session, task):
        """
        关注频道任务
        :param session:
        :param task:
        :return:
        """
        data = await self.get(session, 'plantChannelTaskList')
        if data['code'] != '0':
            println('{}, 获取关注频道任务列表失败!'.format(self.account))
            return
        data = data['data']
        channel_list = data['goodChannelList'] + data['normalChannelList']

        for channel in channel_list:
            body = {
                "channelId": channel['channelId'],
                "channelTaskId": channel['channelTaskId']
            }
            res = await self.get(session, 'plantChannelNutrientsTask', body)
            if 'errorCode' in res:
                println('{}, 关注频道结果:{}'.format(self.account, res['errorMessage']))
            else:
                println('{}, 关注频道结果:{}'.format(self.account, res))
            await asyncio.sleep(1)

    @logger.catch
    async def get_friend_nutriments(self, session, page=1):
        """
        获取好友营养液
        :param page:
        :param session:
        :return:
        """
        if page > 3:
            return
        println('{}, 开始收取第{}页的好友营养液!'.format(self.account, page))
        body = {
            'pageNum': str(page),
        }
        data = await self.post(session, 'plantFriendList', body)

        if data['code'] != '0' or 'data' not in data:
            println('{}, 无法获取好友列表!'.format(self.account))
            return

        data = data['data']
        msg = None

        if 'tips' in data:
            println('{}, 今日偷取好友营养液已达上限!'.format(self.account))
            return
        if 'friendInfoList' not in data or len(data['friendInfoList']) < 0:
            println('{}, 当前暂无可以获取的营养液的好友！'.format(self.account))
            return

        for item in data['friendInfoList']:
            if 'nutrCount' not in item or int(item['nutrCount']) <= 1:  # 小于两瓶基本无法活动奖励, 不收
                continue
            body = {
                'roundId': self.cur_round_id,
                'paradiseUuid': item['paradiseUuid']
            }
            res = await self.post(session, 'collectUserNutr', body)
            if res['code'] != '0' or 'errorMessage' in res:
                println('{}, 帮:{}收取营养液失败!'.format(self.account, item['plantNickName']))
                continue

            println(self.account, res['data']['collectMsg'])
            await asyncio.sleep(0.5)  # 短暂延时，避免出现活动火爆

        if not msg:
            println('{}, 第{}页好友没有可收取的营养液!'.format(self.account, page))

        await asyncio.sleep(1)
        await self.get_friend_nutriments(session, page+1)

    @println_task
    async def evaluation_goods_task(self, session, task):
        """
        :param session:
        :param task:
        :return:
        """
        println('{}, 任务:{}, 请手动前往APP完成任务！'.format(self.account, task['taskName']))

    @println_task
    async def visit_meeting_place_task(self, session, task):
        """
        逛会场
        :param session:
        :param task:
        :return:
        """
        data = await self.post(session, 'receiveNutrientsTask', {"awardType": '4'})
        println('{}, {}:{}'.format(self.account, task['taskName'], data))

    @println_task
    async def free_fruit_task(self, session, task):
        """
        免费水果任务
        :param session:
        :param task:
        :return:
        """
        data = await self.post(session, 'receiveNutrientsTask', {"awardType": '36'})
        println('{}, {}:{}'.format(self.account, task['taskName'], data))

    @println_task
    async def jx_red_packet(self, session, task):
        """
        京喜红包
        :param session:
        :param task:
        :return:
        """
        data = await self.post(session, 'receiveNutrientsTask', {"awardType": '33'})
        println('{}, {}:{}'.format(self.account, task['taskName'], data))

    @println_task
    async def double_sign_task(self, session, task):
        """
        京喜双签
        :param session:
        :param task:
        :return:
        """
        data = await self.post(session, 'receiveNutrientsTask', {"awardType": '7'})
        println('{}, {}:{}'.format(self.account, task['taskName'], data))

    async def get_share_code(self, session):
        """
        获取助力码
        :return:
        """
        data = await self.post(session=session, function_id='plantBeanIndex')
        if not data or data['code'] != '0' or 'errorMessage' in data:
            println('{}, 获取助力码失败:{}'.format(self.account, data.get('errorMessage', '未知')))
            return None
        share_url = furl(data['data']['jwordShareInfo']['shareUrl'])
        code = share_url.args.get('plantUuid', '')
        println('{} 助力码:{}'.format(self.account, code))
        Code.insert_code(code_key=CODE_PLANTING_BEAN, code_val=code, account=self.account, sort=self.sort)
        return code

    async def help_friend(self, session):
        """
        助力好友任务
        :param session:
        :return:
        """
        item_list = Code.get_code_list(code_key=CODE_PLANTING_BEAN)
        item_list.extend(get_code_list(CODE_PLANTING_BEAN))
        for item in item_list:
            friend_account, friend_code = item.get('account'), item.get('code')
            if self.account == friend_account:
                continue
            body = {
                "plantUuid": friend_code,
                "wxHeadImgUrl": "",
                "shareUuid": "",
                "followType": "1",
            }
            data = await self.post(session, 'plantBeanIndex', body)
            message = '{}, 助力好友{}, 结果:{}'
            if data['code'] == '0':
                if 'helpShareRes' not in data:
                    message = message.format(self.account, friend_account, '未知')
                    println(message)
                    continue

                if data['data']['helpShareRes']['state'] == '2':
                    message = message.format(self.account, friend_account, '您今日助力的机会已耗尽，已不能再帮助好友助力了!')
                    println(message)
                    break
                elif data['data']['helpShareRes']['state'] == '3':
                    message = message.format(self.account, friend_account, '该好友今日已满9人助力/20瓶营养液,明天再来为Ta助力吧')
                else:
                    message = message.format(self.account,  friend_account, data['data']['helpShareRes']['promptText'])
                println(message)
            else:
                message = message.format(self.account, message, '原因未知!')
                println(message)
            await asyncio.sleep(1)

    async def do_tasks(self, session):
        """
        做任务
        :param session:
        :return:
        """
        task_map = {
            1: self.receive_nutrient_task,  # 每日签到
            # 2: self.help_friend_task,  # 助力好友
            3: self.visit_shop_task,  # 浏览店铺
            # 4: self.visit_meeting_place_task,  # 逛逛会场
            5: self.pick_goods_task,  # 挑选商品
            # 7: self.double_sign_task,  # 金融双签
            8: self.evaluation_goods_task,  # 评价商品,
            10: self.focus_channel_task,  # 关注频道,
            33: self.jx_red_packet,  # 京喜红包
            36: self.free_fruit_task  # 免费水果

        }
        for task in self.task_list:
            if task['isFinished'] == 1:
                println('{}, 任务:{}, 今日已领取过奖励, 不再执行...'.format(self.account, task['taskName']))
                continue
            if task['taskType'] in task_map:
                task['account'] = self.account
                await task_map[task['taskType']](session, task)
            else:
                data = await self.post(session, 'receiveNutrientsTask', {"awardType": str(task['taskType'])})
                println('{}, {}:{}'.format(self.account, task['taskName'], data))

            await asyncio.sleep(0.2)

    async def collect_nutriments(self, session):
        """
        收取营养液
        :return:
        """
        # 刷新数据
        await self.planting_bean_index(session)
        await asyncio.sleep(0.1)
        if not self.cur_round_list or 'roundState' not in self.cur_round_list:
            println('{}, 获取营养池数据失败, 无法收取！'.format(self.account))

        if self.cur_round_list['roundState'] == '2':
            for item in self.cur_round_list['bubbleInfos']:
                body = {
                    "roundId": self.cur_round_id,
                    "nutrientsType": item['nutrientsType'],
                }
                res = await self.post(session, 'cultureBean', body)
                println('{}, 收取-{}-的营养液, 结果:{}'.format(self.account, item['name'], res))
                await asyncio.sleep(1)
            println('{}, 收取营养液完成！'.format(self.account))
        else:
            println('{}, 暂无可收取的营养液！'.format(self.account))

    async def get_reward(self, session):
        """
        获取奖励
        :param session:
        :return:
        """
        await self.planting_bean_index(session)
        await asyncio.sleep(0.2)
        if not self.prev_round_list:
            println('{}, 无法获取上期活动信息!'.format(self.account))

        if self.prev_round_list['awardState'] == '6':
            self.message += '【上期兑换京豆】{}个!\n'.format(self.prev_round_list['awardBeans'])
        elif self.prev_round_list['awardState'] == '4':
            self.message += '【上期状态】{}\n'.format(self.prev_round_list['tipBeanEndTitle'])
        elif self.prev_round_list['awardState'] == '5':
            println('{}, 开始领取京豆!'.format(self.account))
            body = {
                "roundId": self.prev_round_list['roundId']
            }
            res = await self.post(session, 'receivedBean', body)
            if res['code'] != '0':
                self.message += '【上期状态】查询异常:{}\n'.format(self.prev_round_list)
            else:
                self.message += '【上期兑换京豆】{}个\n'.format(res['data']['awardBean'])
        else:
            self.message += '【上期状态】查询异常:{}\n'.format(self.prev_round_list)

        self.message += f'【本期时间】:{self.cur_round_list["dateDesc"].replace("上期 ", "")}\n'
        self.message += f'【本期成长值】:{self.cur_round_list["growth"]}\n'

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            is_success = await self.planting_bean_index(session)
            if not is_success:
                println('{}, 无法获取活动数据!'.format(self.account))
                return
            self.share_code = await self.get_share_code(session)  # 获取当前账号助力码
            await self.receive_nutrient(session)
            await self.do_tasks(session)
            await self.get_friend_nutriments(session)
            await self.collect_nutriments(session)
            await self.get_reward(session)

    async def run_help(self):
        """
        助力入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.help_friend(session)


if __name__ == '__main__':
    process_start(JdPlantingBean, '种豆得豆', code_key=CODE_PLANTING_BEAN)
