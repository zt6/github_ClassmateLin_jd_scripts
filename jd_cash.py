#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/8 5:43 下午
# @File    : jd_cash.py
# @Project : jd_scripts
# @Cron    : 46 */12 * * *
# @Desc    : 京东APP->搜索领现金进入
import aiohttp
import asyncio

import json
from urllib.parse import quote
from utils.console import println
from utils.process import process_start
from utils.jd_init import jd_init
from utils.logger import logger
from utils.process import get_code_list
from db.model import Code

# 领现金助力码
CODE_JD_CASH = 'jd_cash'


@jd_init
class JdCash:
    """
    签到领现金
    """
    headers = {
        'Accept-Language': 'zh-cn',
        'Accept-Encoding': 'gzip, deflate, br',
        'Host': 'api.m.jd.com',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Referer': 'https://wq.jd.com/wxapp/pages/hd-interaction/index/index',
    }
    code = None

    async def request(self, session, function_id, body=None):
        """
        :param session:
        :param function_id:
        :param body:
        :return:
        """
        if body is None:
            body = {}
        url = 'https://api.m.jd.com/client.action?functionId={}&body={}' \
              '&appid=CashRewardMiniH5Env&clientVersion=9.2.8'.format(function_id, quote(json.dumps(body)))
        try:
            response = await session.get(url=url)
            text = await response.text()
            data = json.loads(text)
            return data
        except Exception as e:
            println('{}, 获取服务器数据失败:{}!'.format(self.account, e.args))
            return {
                'code': 9999,
                'data': {
                    'bizCode': 9999
                }
            }

    @logger.catch
    async def get_task_list(self, session):
        """
        :param session:
        :return:
        """
        try:
            session.headers.add('Host', 'api.m.jd.com')
            session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
            session.headers.add('User-Agent',
                                'okhttp/3.12.1;jdmall;android;version/10.0.6;build/88852;screen/1080x2293;os/11'
                                ';network/wifi;')
            url = 'https://api.m.jd.com/client.action?functionId=cash_homePage&clientVersion=10.0.6&build=88852&client' \
                  '=android&d_brand=realme&d_model=RMX2121&osVersion=11&screen=2293*1080&partner=oppo&oaid=&openudid' \
                  '=a27b83d3d1dba1cc&eid=eidA1a01812289s8Duwy8MyjQ9m/iWxzcoZ6Ig7sNGqHp2V8/mtnOs' \
                  '+KCpWdqNScNZAsDVpNKfHAj3tMYcbWaPRebvCS4mPPRels2DfOi9PV0J+/ZRhX&sdkVersion=30&lang=zh_CN&uuid' \
                  '=a27b83d3d1dba1cc&aid=a27b83d3d1dba1cc&area=19_1601_36953_50397&networkType=wifi&wifiBssid=unknown' \
                  '&uts=0f31TVRjBStRmxA4qmf9RVgENWVO2TGQ2MjkiPwRvZZIAsHZydeSHYcTNHWIbLF17jQfBcdAy' \
                  '%2BSBzhNlEJweToEyKpbS1Yp0P0AKS78EpxJwB8v%2BZSdypE%2BhFoHHlcMyF4pc0QIWs%2B85gCH%2BHp9' \
                  '%2BfP8lKG5QOgoTBOjLn0U5UOXWFvVJlEChArvBygDg6xpmSrzN6AMVHTXrbpV%2FYbl4FQ%3D%3D&uemps=0-0&harmonyOs' \
                  '=0&st=1625744661962&sign=c8b023465a9ec1e9b912ac3f00a36377&sv=110&body={}'.format(
                quote(json.dumps({})))
            response = await session.post(url=url)
            text = await response.text()
            data = json.loads(text)
            if data['code'] != 0 or data['data']['bizCode'] != 0:
                return []
            return data['data']['result']['taskInfos']
        except Exception as e:
            println('{}, 获取任务列表失败:{}!'.format(self.account, e.args))
            return []

    async def get_wx_task_list(self, session):
        """
        获取微信小程序里面的任务
        :param session:
        :return:
        """
        res = await self.request(session, 'cash_mob_home', {"isLTRedPacket": "1"})
        if res['code'] != 0 or res['data']['bizCode'] != 0:
            return []
        return res['data']['result']['taskInfos']

    @logger.catch
    async def get_share_code(self, session):
        """
        获取助力码
        :return:
        """
        data = await self.request(session, 'cash_getJDMobShareInfo', {"source": 2})
        if data['code'] != 0 or data['data']['bizCode'] != 0:
            return None
        else:
            data = data['data']['result']
            share_code = data['inviteCode'] + '@' + data['shareDate']

        println('{}, 助力码:{}'.format(self.account, share_code))
        Code.insert_code(code_key=CODE_JD_CASH, code_val=share_code, account=self.account, sort=self.sort)
        return share_code

    @logger.catch
    async def init(self, session):
        """
        获取首页数据
        :return:
        """
        data = await self.request(session, 'cash_mob_home')
        if data['code'] != 0 or data['data']['bizCode'] != 0:
            println('{}, 初始化数据失败!'.format(self.account))
            return False
        data = data['data']['result']
        self.code = data['inviteCode'] + '@' + data['shareDate']
        return True

    @logger.catch
    async def do_tasks(self, session, times=4):
        """
        做任务
        :param times:
        :param session:
        :return:
        """
        if times <= 0:
            return

        task_list = await self.get_task_list(session)
        wx_task_list = await self.get_wx_task_list(session)
        task_list.extend(wx_task_list)

        for task in task_list:
            if task['finishFlag'] == 1:
                println('{}, 任务:《{}》, 今日已完成!'.format(self.account, task['name']))
                continue
            if task['type'] == 4:
                task_info = task['jump']['params']['skuId']
            elif task['type'] == 7:
                task_info = 1
            elif task['type'] == 2:
                task_info = task['jump']['params']['shopId']
            elif task['type'] in [16, 3, 5, 17, 21]:
                task_info = task['jump']['params']['url']
            # elif task['type'] in [30, 31]:
            #     task_info = task['jump']['params']['path']
            else:

                println('{}, 跳过任务:《{}》!'.format(self.account, task['name']))
                continue

            println('{}, 正在进行任务:《{}》, 进度:{}/{}!'.format(self.account, task['name'], task['doTimes'], task['times']))
            res = await self.request(session, 'cash_doTask', {
                'type': task['type'],
                'taskInfo': task_info
            })
            await asyncio.sleep(1)

            if res['code'] != 0 or res['data']['bizCode'] != 0:
                println('{}, 任务:《{}》完成失败, {}!'.format(self.account, task['name'], res['data']['bizMsg']))
            else:
                println('{}, 成功完成任务:《{}》!'.format(self.account, task['name']))
        await self.do_tasks(session, times - 1)

    @logger.catch
    async def get_award(self, session):
        """
        领取奖励
        :param session:
        :return:
        """
        for i in [1, 2]:
            data = await self.request(session, 'cash_mob_reward', {"source": i, "rewardNode": ""})
            if data['code'] != 0 or data['data']['bizCode'] != 0:
                println(data)
                println('{}, 领取奖励失败!'.format(self.account))
            else:
                println('{}, 成功领取奖励!'.format(self.account))
            await asyncio.sleep(2)

    @logger.catch
    async def help_friend(self, session):
        """
        :param session:
        :return:
        """
        session.headers.add('Referer', 'https://h5.m.jd.com/babelDiy/Zeus/GzY6gTjVg1zqnQRnmWfMKC4PsT1/index.html')

        item_list = Code.get_code_list(code_key=CODE_JD_CASH)
        item_list.extend(get_code_list(CODE_JD_CASH))
        for item in item_list:
            friend_account, friend_code = item.get('account'), item.get('code')
            if friend_account == self.account:
                continue

            invite_code, share_date = friend_code.split('@')

            data = await self.request(session, 'cash_mob_assist', {"inviteCode": invite_code,
                                                                   "shareDate": share_date, "source": 2})
            if data['code'] != 0 or data['data']['bizCode'] != 0:
                println('{}, 助力好友:{}失败, {}！'.format(self.account, invite_code, data['data']['bizMsg']))
                if data['data']['bizCode'] in [206, 188]:  # 助力次数用完/活动太火爆了
                    break
            else:
                println('{}, 助力好友:{}成功!'.format(self.account, invite_code))

            await asyncio.sleep(2.5)

    async def sign(self, session):
        """
        签到
        :param session:
        :return:
        """
        try:
            url = 'https://api.m.jd.com/client.action?functionId=cash_sign&clientVersion=10.0.11&build=89314&client' \
                  '=android&osVersion=11&partner=jingdong&openudid=a27b83d3d1dba1cc&sdkVersion=30&uuid=a27b83d3d1dba1cc' \
                  '&aid=a27b83d3d1dba1cc&networkType=wifi&st=1628419999801&sign=9c2543218680da1f16e0a36afb8c5ba1&sv=100' \
                  '&body=%7B%22breakReward%22%3A0%2C%22inviteCode%22%3Anull%2C%22remind%22%3A0%2C%22type%22%3A0%7D&'
            response = await session.post(url)
            text = await response.text()
            data = json.loads(text)
            println('{}, 签到结果;{}!'.format(self.account, data['data']['bizMsg']))
        except Exception as e:
            println('{}, 签到异常, {}'.format(self.account, e.args))

    async def withdraw_ten(self, session):
        """
        提现10元
        :return:
        """
        try:
            url = 'https://api.m.jd.com/client.action?functionId=cash_wx_withdraw&clientVersion=10.0.11&build=89314' \
                  '&client=android&screen=2293*1080&partner=jingdong&oaid=&openudid=a27b83d3d1dba1cc&sdkVersion=30' \
                  '&lang=zh_CN&uuid=a27b83d3d1dba1cc&aid=a27b83d3d1dba1cc&networkType=wifi&st=1628420578663&sign' \
                  '=9dc459ed7419420373445f67bbd6c12b&sv=122&body=%7B%22amount%22%3A1000%2C%22code%22%3A%22001nc' \
                  'QFa1THZwB0muVFa16WXOe0ncQFm%22%7D&'
            response = await session.post(url)
            text = await response.text()
            data = json.loads(text)
            println('{}, 提现10元结果{}!'.format(self.account, data['data']['bizMsg']))
        except Exception as e:
            println('{}, 提现10元异常, {}'.format(self.account, e.args))

    async def run(self):
        """
        入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            success = await self.init(session)
            if not success:
                println('{}, 无法初始化数据, 退出程序!'.format(self.account))
                return
            await self.sign(session)
            await self.get_share_code(session)
            await self.do_tasks(session)
            # await self.get_award(session)
            await self.withdraw_ten(session)

    async def run_help(self):
        """GetSuggestContent?zone=dream_factory&type=1&_time=1628418529947&_stk=_time%2Ctype%2Czone&_ste=1&h5st=20210808182849947%3B4637489386822162%3B10001%3Btk01w9d981bd9a8nU3BBZnNWbHpVdP%2BPHSAkpQ8STHtPYCGIoNHoE4qjMHxdHfHS%2BsnSiGY6mMv%2FRkxxrPkap3g6947E%3Bf98c48ae6521045a461eaa18e9bd1bd3c584c493b1880540dbc19533b0cc7da1&_=1628418529952&sceneval=2&g_login_type=1&callback=jsonpCBKU&g_ty=ls
        助力入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.help_friend(session)


if __name__ == '__main__':
    process_start(JdCash, '签到领现金', code_key=CODE_JD_CASH)
