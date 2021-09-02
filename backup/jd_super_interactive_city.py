#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/29 上午11:36
# @Project : jd_scripts
# @File    : jd_super_interactive_city.py
# @Cron    : # 5 9 * * *
# @Desc    : 超级互动城
import asyncio
import datetime
import json

import aiohttp

from urllib.parse import urlencode

from config import USER_AGENT

from utils.process import process_start
from utils.logger import logger
from utils.console import println
from utils.jd_init import jd_init


@jd_init
class JdSuperInteractiveCity:

    headers = {
        'origin': 'https://lzkj-isv.isvjcloud.com',
        'content-type': 'application/x-www-form-urlencoded',
        'referer': 'https://lzkj-isv.isvjcloud.com/wxCollectionActivity/activity2/',
        'user-agent': USER_AGENT,
    }

    lz_token_key = None
    lz_token_val = None
    isv_token = None
    pin = None
    nickname = None

    async def request(self, session, path='/', form=None, method='POST'):
        """
        请求数据
        :param method:
        :param path:
        :param form:
        :param session:
        :return:
        """
        try:
            url = 'https://lzkj-isv.isvjcloud.com/' + path
            if form:
                url += '?' + urlencode(form)
            if method == 'POST':
                response = await session.post(url)
            else:
                response = await session.get(url)

            text = await response.text()

            data = json.loads(text)

            return data
        except Exception as e:
            println(e.args)

    async def get_wx_common_token(self, session):
        """
        获取token
        :param session:
        :return:
        """
        res = await self.request(session, 'wxCommonInfo/token')
        if not res.get('result'):
            return
        self.lz_token_key = res['data']['LZ_TOKEN_KEY']
        self.lz_token_val = res['data']['LZ_TOKEN_VALUE']
        println('{}, lz_token:{}'.format(self.account, self.lz_token_val))

    async def get_isv_obfuscator_token(self, session):
        """
        获取isv token
        :param session:
        :return:
        """
        try:
            url = 'https://api.m.jd.com/client.action?functionId=isvObfuscator&&body=%7B%22url%22%3A%22https%3A%5C/%5C' \
                  '/lzdz1-isv.isvjcloud.com%22%2C%22id%22%3A%22%22%7D&build=167764&client=apple&clientVersion=10.0.10' \
                  '&d_brand=apple&d_model=iPhone12%2C1&eid=eidIeb54812323sf%2BAJEbj5LR0Kf6GUzM9DKXvgCReTpKTRyRwiuxY' \
                  '/uvRHBqebAAKCAXkJFzhWtPj5uoHxNeK3DjTumb%2BrfXOt1w0/dGmOJzfbLuyNo&isBackground=N&joycious=68&lang=zh_CN' \
                  '&networkType=wifi&networklibtype=JDNetworkBaseAF&openudid=8a0d1837f803a12eb217fcf5e1f8769cbb3f898d' \
                  '&osVersion=14.3&partner=apple&rfs=0000&scope=11&screen=828%2A1792&sign' \
                  '=3c9b9db164cc8d694603ca6e3d7fb003&st=1628423908868&sv=102&uemps=0-0&uts=0f31TVRjBSuihfC/1D' \
                  '/2G8oVbUW0Pu4uJDif0Ehi7AVzM40fF9GfNX0yawFyBpTXK/PgWitxArFfBLGK' \
                  '%2Be2W5Pno6b7J4iivmXiQYbYPZi7fbVYEHb8Xa5JAi/fbdr/QeztGPJhLoPHKsXGU39PgzC1cWUEVezUyvHVtAuVQGBR' \
                  '%2Bj6Cx5kcez%2BkVn3IH8dKrAI6kA/Ct%2BQopU%2BROo1oY2w%3D%3D&uuid=hjudwgohxzVu96krv/T6Hg%3D%3D'
            response = await session.post(url)
            text = await response.text()
            res = json.loads(text)
            if res.get('code') == '0':
                self.isv_token = res['token']
                println('{}, isv_token:{}'.format(self.account, self.isv_token))
        except Exception as e:
            logger.error('{}, 获取isv_token失败, {}'.format(self.account, e.args))

    async def get_act_user_id(self, session, activity_id='0b1dd1821ab14e9a8ab4fa220df723f0'):
        """
        获取活动的用户ID
        :return:
        """
        res = await self.request(session, '/customer/getSimpleActInfoVo', {
            'activityId': activity_id
        })
        if res.get('result'):
            return res['data']['venderId']
        else:
            return None

    async def get_my_ping(self, session, act_user_id=None):
        """
        获取pin
        :return:
        """
        res = await self.request(session, '/customer/getMyPing', {
            'userId': act_user_id,
            'token': self.isv_token,
            'fromType': 'APP'
        })
        if not res.get('result'):
            return

        self.pin = res['data']['secretPin']
        self.nickname = res['data']['nickname']

    async def has_signed(self, session, act_id, vender_id):
        """
        判断是否已经签到
        :param session:
        :return:
        """
        res = await self.request(session, '/sign/wx/getSignInfo', {
            'venderId': vender_id,
            'pin': self.pin,
            'actId': act_id
        })
        if not res.get('isOk'):
            return False
        date = datetime.datetime.now().strftime('%Y%m%d')
        if res.get('signDetail', dict()).get(date, 'n') == 'y':
            return True
        return False

    async def get_sign_act_info(self, session, act_id, vendor_id):
        """
        获取签到活动详情
        :param vendor_id:
        :param act_id:
        :param session:
        :return:
        """
        res = await self.request(session, '/sign/wx/getActivity', {
            'actId': act_id,
            'venderId': vendor_id
        })
        if res.get('isOk'):
            return res['act']
        else:
            return None

    async def get_shop_sign_list(self, session, page=50):
        """
        获取店铺签到列表
        :param session:
        :param page:
        :return:
        """
        shop_list = []
        for p in range(1, page):
            println('{}, 正在获取第{}页店铺列表!'.format(self.account, p))
            res = await self.request(session, '/wxAssemblePage/getTopAndNewActInfo', {
                'pin': self.pin,
                'aggrateActType': 5,
                'topNewType': 1,
                'pageNo': p,
                'pageSize': 20
            })
            if not res.get('result'):
                println('{}, 获取店铺列表失败!')
                return
            item_list = res['data']['homeInfoResultVOList']

            for item in item_list:
                println('{}, 正在获取店铺{}签到活动!'.format(self.account, item['shopName']))
                act_id = item['activityId']
                vendor_id = item['venderId']
                act_info = await self.get_sign_act_info(session, act_id, vendor_id)
                await asyncio.sleep(2)
                if not act_info or '活动对象：店铺会员' in str(act_info) or '京豆' not in str(act_info['giftJson']):
                    continue

                shop_list.append({
                    'act_id': item['activityId'],
                    'vendor_id': item['venderId'],
                    'shop_name': item['shopName']
                })
            await asyncio.sleep(20)
        println(shop_list)

    async def shop_sign(self, session):
        """
        店铺签到
        :param session:
        :return:
        """
        await self.get_shop_sign_list(session)
        # has_signed = await self.has_signed(session, act_id, vendor_id)
        # if has_signed:
        #     println('{}, 店铺{}今日已签到!'.format(self.account, item['shopName']))
        #     continue
        # res = await self.request(session, '/sign/wx/signUp', {
        #     'actId': act_id,
        #     'pin': self.pin,
        # })
        # println(res)
        # await asyncio.sleep(20)

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.get_wx_common_token(session)
            await self.get_isv_obfuscator_token(session)
            if not self.lz_token_key or not self.lz_token_val or not self.isv_token:
                println('{}, 获取TOKEN失败, 退出程序!'.format(self.account))
                return

        self.cookies['IsvToken'] = self.isv_token
        self.cookies['LZ_TOKEN_KEY'] = self.lz_token_key
        self.cookies['LZ_TOKEN_VALUE'] = self.lz_token_val
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            user_id = await self.get_act_user_id(session)
            await self.get_my_ping(session, user_id)
            await self.shop_sign(session)


if __name__ == '__main__':
    from config import JD_COOKIES
    app = JdSuperInteractiveCity(**JD_COOKIES[0])
    asyncio.run(app.run())
