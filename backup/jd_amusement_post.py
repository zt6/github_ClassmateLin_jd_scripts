#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/2 下午9:50
# @Project : jd_scripts
# @File    : jd_amusement_post.py
# @Cron    : 45 8,15 * * *
# @Desc    : 京东APP->签到领豆->边玩边赚->京小鸽游乐寄
import asyncio
import json

import ujson
import aiohttp
from config import USER_AGENT
from utils.jd_init import jd_init
from utils.console import println
from utils.logger import logger
from db.model import Code

# 京小鸽游乐寄助力码
CODE_AMUSEMENT_POST = 'amusement_post'


@jd_init
class JdAmusementPost:
    """
    京小鸽游乐寄
    """
    headers = {
        'origin': 'https://jingcai-h5.jd.com',
        'user-agent': 'jdapp;' + USER_AGENT,
        'lop-dn': 'jingcai.jd.com',
        'accept': 'application/json, text/plain, */*',
        'appparams': '{"appid":158,"ticket_type":"m"}',
        'content-type': 'application/json',
        'referer': 'https://jingcai-h5.jd.com/index.html'
    }

    async def request(self, session, path, body=None, method='POST'):
        """
        请求数据
        :return:
        """
        try:
            if not body:
                body = {}
            url = 'https://lop-proxy.jd.com/' + path
            if method == 'POST':
                response = await session.post(url, json=body)
            else:
                response = await session.get(url, json=body)

            text = await response.text()
            data = json.loads(text)
            return data

        except Exception as e:
            println('{}, 请求服务器数据失败, {}'.format(self.account, e.args))
            return {
                'success': False
            }

    @logger.catch
    async def get_index_data(self, session):
        """
        获取首页数据
        :return:
        """
        res = await self.request(session, 'MangHeApi/queryRuleInfo', [{
            "userNo": "$cooMrdGatewayUid$"
        }])
        success = res.get('success', False)
        if not success:
            return None
        return res['content']

    @logger.catch
    async def get_card(self, session, code):
        """
        领取卡片
        :param code:
        :param session:
        :return:
        """
        body = [{
            "userNo": "$cooMrdGatewayUid$",
            "getCode": code,
        }]
        res = await self.request(session, 'MangHeApi/getCard', body)
        success = res.get('success', False)
        if success:
            println('{}, 成功领取1张卡片!'.format(self.account))
        else:
            println('{}, 领取卡片失败!'.format(self.account))

    @logger.catch
    async def sign(self, session):
        """
        每日签到
        :param session:
        :return:
        """
        res = await self.request(session, '/mangHeApi/signIn', [{
            "userNo": "$cooMrdGatewayUid$"
        }])
        success = res.get('success', False)
        if not success:
            println('{}, 签到失败, {}!'.format(self.account, res.get('msg', '原因未知')))
        else:
            println('{}, 签到成功!'.format(self.account))

    @logger.catch
    async def visit_jc(self, session):
        """
        访问精彩
        :param session:
        :return:
        """
        body = [{
            "userNo": "$cooMrdGatewayUid$"
        }]
        await self.request(session, 'mangHeApi/setUserHasView', body)

    @logger.catch
    async def run_help(self):
        """
        执行助力
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:

            code_list = Code.get_code_list(code_key=CODE_AMUSEMENT_POST)
            if not code_list:
                return
            for code in code_list:
                friend_account = code.get('account')
                friend_code = code.get('code')
                if friend_account == self.account:
                    continue
                res = await self.request(session, 'MangHeApi/helpFriend', [{
                    "userNo": "$cooMrdGatewayUid$",
                    "missionNo": friend_code
                }])
                success = res.get('success', False)
                if success:
                    println('{}, 成功助力好友:{}!'.format(self.account, friend_account))
                else:
                    println('{}, 无法助力好友:{}!'.format(self.account, friend_account))

    async def synthesis(self, session):
        """
        合卡
        :return:
        """
        res = await self.request(session, '/MangHeApi/synthesize', [{
            "userNo": "$cooMrdGatewayUid$"
        }])
        if res.get('success', False):
            println('{}, 成功合成一张抽奖卡, 去抽奖...'.format(self.account))
        else:
            println('{}, 无法合成抽奖卡，卡片不足!'.format(self.account))
            return

        res = await self.request(session, '/MangHeApi/getBigReward', [{
            "userNo": "$cooMrdGatewayUid$"
        }])
        println('{}, 抽奖结果:{}!'.format(self.account, res.get('content', '未知')))

    async def get_share_code(self, session):
        """
        获取助力码
        :return:
        """
        res = await self.request(session, 'MangHeApi/newShare', [{
            "userNo": "$cooMrdGatewayUid$"
        }])
        code = res.get('data', None)
        if code:
            println('{}, 助力码:{}'.format(self.account, code))
            Code.insert_code(code_key=CODE_AMUSEMENT_POST, code_val=code, account=self.account,
                             sort=self.sort)
        return code

    @logger.catch
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies,
                                         json_serialize=ujson.dumps) as session:
            data = await self.get_index_data(session)
            if not data:
                println('{}, 无法获取活动首页数据, 退出!'.format(self.account))
                return
            await self.get_share_code(session)
            for item in data:
                if item['status'] == 10:
                    println('{}, 今日已领取过《{}》的卡片!'.format(self.account, item['name']))
                    continue
                jump_type = item.get('jumpType')
                if jump_type == 41:
                    await self.visit_jc(session)
                    await asyncio.sleep(1)
                elif jump_type == 31:
                    await self.sign(session)
                    await asyncio.sleep(1)

            data = await self.get_index_data(session)

            for item in data:
                if item['status'] == 11:
                    for no in item['getRewardNos']:
                        await self.get_card(session, no)
                        await asyncio.sleep(1)

            await self.synthesis(session)


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdAmusementPost, '京小鸽-游乐寄', code_key=CODE_AMUSEMENT_POST)
