#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/5 9:34 上午
# @File    : jd_sign.py
# @Project : jd_scripts
# @Cron    : 0 3,19 * * *
# @Desc    : 京东签到合集
import json
import aiohttp
import re

from urllib.parse import quote
from utils.console import println
from utils.jd_init import jd_init
from config import USER_AGENT


@jd_init
class JdSign:

    headers = {
        'user-agent': 'jdapp;' + USER_AGENT
    }

    async def request(self, session, url, method='POST'):
        """
        请求数据
        :param url:
        :param session:
        :param method:
        :return:
        """
        try:
            if method == 'POST':
                response = await session.post(url)
            else:
                response = await session.get(url)

            text = await response.text()

            data = json.loads(text)

            return data

        except Exception as e:
            println('{}, 请求服务器数据失败,{}!'.format(self.account, e.args))

    async def bean_sign(self, session):
        """
        领京豆-签到
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=signBeanIndex&body=%7B%22monitor_refer%22%3A%22%22%2C' \
              '%22rnVersion%22%3A%223.9%22%2C%22fp%22%3A%22-1%22%2C%22shshshfp%22%3A%22-1%22%2C%22shshshfpa%22%3A%22' \
              '-1%22%2C%22referUrl%22%3A%22-1%22%2C%22userAgent%22%3A%22-1%22%2C%22jda%22%3A%22-1%22%2C' \
              '%22monitor_source%22%3A%22bean_m_bean_index%22%7D&appid=ld&client=apple&clientVersion=10.0.11' \
              '&networkType=wifi&osVersion=14&uuid=1623732683334633-4613462616133636&eu=1623732683334633&fv' \
              '=4613462616133636&jsonp='

        res = await self.request(session, url)

        if res.get('code', '-1') != '0':
            println('{}, 签到京豆签到失败!'.format(self.account))
            return

        status = int(res.get('data', dict()).get('status', '-1'))

        if status == 1:
            println('{}, 签到京豆签到成功!'.format(self.account))

        elif status == 2:
            println('{}, 签到京豆今日已签到!'.format(self.account))

        else:
            println('{}, 签到京豆签到失败!'.format(self.account))

    async def jd_shop(self, session, name='', body=''):
        """
         京东商城签到
        :param body:
        :param name:
        :param session:
        :return:
        """
        url = 'https://api.m.jd.com/?client=wh5&functionId=qryH5BabelFloors'
        session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            sign_params = None
            turn_table_id = None

            if 'qxTid' in data and data['qxTid']:
                turn_table_id = data['qxTid']

            if 'floorList' in data and data['floorList']:
                for floor in data['floorList']:
                    if 'boardParams' in floor and 'turnTableId' in floor['boardParams']:
                        turn_table_id = floor['boardParams']['turnTableId']

            if 'qxAct' in data:
                sign_params = data['qxAct']

            if 'floatLayerList' in data and data['floatLayerList']:
                float_layer_text = json.dumps(data['floatLayerList'])
                if len(re.findall('enActK', float_layer_text)) > 0:
                    for float_layer in data['floatLayerList']:
                        if 'params' in float_layer:
                            sign_params = {
                                'params': float_layer['params']
                            }

            if 'floorList' in data and data['floorList']:
                for floor in data['floorList']:
                    if floor['template'] == 'signIn':
                        sign_info = floor['signInfos']
                        if sign_info['signStat'] == '1':
                            println('{}, {}今日已签到!'.format(self.account, name))
                            return
                        sign_params = {
                            'params': sign_info['params']
                        }  # 签到数据

            if not sign_params and not turn_table_id:
                println('{}, 未找到活动:{}!'.format(self.account, name))
                return

            if turn_table_id:  # 关注店铺
                await self.jd_shop_focus(session, name, turn_table_id)

            if sign_params:  # 去签到
                await self.jd_shop_sign(session, name, sign_params)

        except Exception as e:
            println('{}, 异常:{}'.format(name, e.args))

    async def jd_shop_sign(self, session, name, body):
        """
        :param session:
        :param name:
        :param body:
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=userSign'
        body = 'body={}&client=wh5'.format(quote(json.dumps(body)))
        session.headers.add('Content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)

            if len(re.findall('签到成功', text)):
                println('{}, {}签到成功!'.format(self.account, name))
            elif len(re.findall('已签到', text)):
                println('{}, {}今日已签到!'.format(self.account, name))
            else:
                println('{}, {}签到失败!'.format(self.account, name))
        except Exception as e:
            println('{}, {}签到异常异常:{}'.format(self.account, name, e.args))

    async def jd_shop_focus(self, session, name, tid):
        """
        京东商城店铺关注
        :param tid:
        :param session:
        :param name:
        :return:
        """
        url = 'https://jdjoy.jd.com/api/turncard/channel/detail?turnTableId={}&invokeKey=SkzHkBfmSJdn5rQS'.format(tid)
        try:
            await session.get(url)
            url = 'https://jdjoy.jd.com/api/turncard/channel/sign?invokeKey=SkzHkBfmSJdn5rQS'
            body = 'turnTableId={}'.format(tid)
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)

            if data['success']:
                println('{}, {}关注店铺成功!'.format(self.account, name))
            else:
                println('{}, {}关注店铺失败, {}!'.format(self.account, name, data['errorMessage']))

        except Exception as e:
            println('{}, {}关注店铺异常:{}'.format(self.account, name, e.args))

    async def jd_shop_women(self, session):
        """
        京东商城-女装
        :param session:
        :return:
        """
        name = '京东商城-女装'
        body = 'body=%7B%22activityId%22%3A%22DpSh7ma8JV7QAxSE2gJNro8Q2h9%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_card(self, session):
        """
        京东商城-卡包
        :param session:
        :return:
        """
        code = 'body=%7B%22activityId%22%3A%227e5fRnma6RBATV9wNrGXJwihzcD%22%7D'
        name = '京东商城-卡包'
        await self.jd_shop(session, name, code)

    async def jd_shop_book(self, session):
        """
        京东商城-图书
        :param session:
        :return:
        """
        name = '京东商城-图书'
        body = 'body=%7B%22activityId%22%3A%223SC6rw5iBg66qrXPGmZMqFDwcyXi%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_accompany(self, session):
        """
        京东商城-陪伴
        :param session:
        :return:
        """
        name = '京东商城-陪伴'
        body = 'body=%7B%22activityId%22%3A%22kPM3Xedz1PBiGQjY4ZYGmeVvrts%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_suitcase(self, session):
        """
        京东商城-箱包
        :param session:
        :return:
        """
        name = '京东商城-箱包'
        body = 'body=%7B%22activityId%22%3A%22ZrH7gGAcEkY2gH8wXqyAPoQgk6t%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_shoes(self, session):
        """
        京东商城-鞋靴
        :param session:
        :return:
        """
        name = '京东商城-鞋靴'
        body = 'body=%7B%22activityId%22%3A%224RXyb1W4Y986LJW8ToqMK14BdTD%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_food_market(self, session):
        """
        京东商城-菜场
        :param session:
        :return:
        """
        name = '京东商城-菜场'
        body = 'body=%7B%22activityId%22%3A%22Wcu2LVCFMkBP3HraRvb7pgSpt64%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_clothing(self, session):
        """
        京东商城-服饰
        :param session:
        :return:
        """
        name = '京东商城-服饰'
        body = 'body=%7B%22activityId%22%3A%224RBT3H9jmgYg1k2kBnHF8NAHm7m8%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_health(self, session):
        """
        京东商城-健康
        :param session:
        :return:
        """
        name = '京东商城-健康'
        body = 'body=%7B%22activityId%22%3A%22w2oeK5yLdHqHvwef7SMMy4PL8LF%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_second_hand(self, session):
        """
        京东拍拍-二手
        :param session:
        :return:
        """
        name = '京东拍拍-二手'
        body = 'body=%7B%22activityId%22%3A%223S28janPLYmtFxypu37AYAGgivfp%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_shop_school(self, session):
        """
        京东商城-校园
        :param session:
        :return:
        """
        name = '京东商城-校园'
        body = 'body=%7B%22activityId%22%3A%222QUxWHx5BSCNtnBDjtt5gZTq7zdZ%22%7D'
        await self.jd_shop(session, name, body)

    async def jd_kd_sign(self):
        """
        :param pt_pin:
        :param pt_key:
        :return:
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

        async with aiohttp.ClientSession(headers=headers, cookies=self.cookies) as session:
            try:
                url = 'https://lop-proxy.jd.com/jiFenApi/signInAndGetReward'
                body = '[{"userNo":"$cooMrdGatewayUid$"}]'
                response = await session.post(url=url, data=body)
                text = await response.text()
                data = json.loads(text)
                if data['code'] == 1:
                    println('{}, 京东快递签到成功!'.format(self.account))
                elif data['code'] == -1:
                    println('{}, 京东快递今日已签到!'.format(self.account))
                else:
                    println('{}, 京东快递签到失败!'.format(self.account))
            except Exception as e:
                println('{}, 程序出错:{}!'.format(self.account, e.args))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.bean_sign(session)
            await self.jd_shop_women(session)
            await self.jd_shop_card(session)
            await self.jd_shop_book(session)
            await self.jd_shop_accompany(session)
            await self.jd_shop_suitcase(session)
            await self.jd_shop_shoes(session)
            await self.jd_shop_food_market(session)
            await self.jd_shop_clothing(session)
            await self.jd_shop_second_hand(session)
            await self.jd_shop_school(session)
            await self.jd_kd_sign()


if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = JdSign(**JD_COOKIES[0])
    # asyncio.run(app.run())
    from utils.process import process_start
    process_start(JdSign, '京东签到合集')
