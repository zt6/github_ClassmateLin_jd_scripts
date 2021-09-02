#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/19 12:19 下午
# @File    : jd_try.py
# @Project : jd_scripts
# @Cron    : 25 12 * * *
# @Desc    : 京东APP->我的->更多工具->新品试用
import asyncio
import time

import aiohttp
import json
from config import JD_TRY_CID_LIST, JD_TRY_TYPE_LIST, JD_TRY_MIN_PRICE, JD_TRY_GOODS_COUNT, JD_TRY_FILTER_KEYWORDS
from config import USER_AGENT
from utils.jd_init import jd_init
from utils.console import println
from utils.process import process_start
from utils.logger import logger


async def is_can_cry(goods):
    """
    是否符合条件
    :param goods:
    :return:
    """
    # 商品大于设置的最大商品数
    if goods.get('supplyCount', 1) > JD_TRY_GOODS_COUNT:
        return False

    # 价格小于设定最低价格
    if int(goods.get('jdPrice', 0.0)) < JD_TRY_MIN_PRICE:
        return False

    # 商品名称包含排除的关键字
    for key in JD_TRY_FILTER_KEYWORDS:
        if key in goods.get('trialName', ''):
            return False

    return True


@jd_init
class JdTry:
    headers = {
        'user-agent': USER_AGENT,
        'referer': 'https://try.m.jd.com',
    }

    cid_map = {
        "全部商品": "0",
        "家用电器": "737",
        "手机数码": "652,9987",
        "电脑办公": "670",
        "家居家装": "1620,6728,9847,9855,6196,15248,14065",
        "美妆护肤": "1316",
        "服饰鞋包": "1315,1672,1318,11729",
        "母婴玩具": "1319,6233",
        "生鲜美食": "12218",
        "图书音像": "1713,4051,4052,4053,7191,7192,5272",
        "钟表奢品": "5025,6144",
        "个人护理": "16750",
        "家庭清洁": "15901",
        "食品饮料": "1320,12259",
        "更多惊喜": "4938,13314,6994,9192,12473,6196,5272,12379,13678,15083,15126,15980",
    }

    type_map = {
        "全部试用": "0",
        "普通试用": "1",
        "闪电试用": "3",
        "30天试用": "5",
    }

    min_price = 100  # 商品最低价格

    @logger.catch
    async def request(self, session, url, method='GET'):
        """
        请求数据
        :param url:
        :param method:
        :param params:
        :param path:
        :param session:
        :return:
        """
        try:
            if method == 'GET':
                response = await session.get(url)
            else:
                response = await session.post(url)
            text = await response.text()
            return text
        except Exception as e:
            println('{}, 请求付费器数据失败, {}'.format(self.account, e.args))
            return None

    @logger.catch
    async def get_goods_list_by_condition(self, session, type_val, cid_val, page):
        """
        根据条件获取商品列表
        :param session:
        :param cid_val:
        :param type_val:
        :param page:
        :return:
        """
        url = f'https://try.m.jd.com/activity/list?pb=1&cids={cid_val}&page={page}&pageSize=12&type={type_val}&state=0'
        result = []
        try:
            text = await self.request(session, url)
            data = json.loads(text)
            if not data.get('success', False):
                return result
            goods_list = data['data']['data']

            for goods in goods_list:
                if not await is_can_cry(goods):
                    continue
                result.append({
                    'id': goods['id'],
                    'name': goods['trialName'],
                    'source': goods['source'],
                })
            return result
        except Exception as e:
            println('{}, 获取商品列表失败, {}'.format(self.account, e.args))
            return result

    @logger.catch
    async def get_goods_list(self, session, page=10):
        """
        获取商品列表
        :param session:
        :param page:
        :return:
        """
        result = []
        for type_key in JD_TRY_TYPE_LIST:
            type_val = self.type_map.get(type_key, None)
            if not type_val:
                continue
            for cid_key in JD_TRY_CID_LIST:
                cid_val = self.cid_map.get(cid_key, None)
                if not cid_val:
                    continue
                for p in range(1, page+1):
                    goods_list = await self.get_goods_list_by_condition(session, type_val, cid_val, p)
                    println('{}, 成功获取{}-{}第{}页商品!'.format(self.account, type_key, cid_key, p))
                    result.extend(goods_list)
                    await asyncio.sleep(0.5)
        return result

    @logger.catch
    async def trial(self, session, goods):
        """
        申请试用
        :param goods:
        :param session:
        :return:
        """
        try:
            gid = goods['id']
            source = goods['source']
            url = f'https://try.jd.com/migrate/apply?' \
                  f'activityId={gid}&source={source}&_s=m&_={int(time.time() * 1000)}'
            text = await self.request(session, url)
            data = json.loads(text)
            return data
        except Exception as e:
            println('{}, 请求服务器数据错误, {}!'.format(self.account, e.args))
            return 0

    @logger.catch
    async def apply_for_trial(self, session, goods_list):
        """
        申请试用
        :param session:
        :param goods_list:
        :return:
        """
        println(len(goods_list))
        for goods in goods_list:
            data = await self.trial(session, goods)
            println('{}, 商品:《{}》, {}'.format(self.account, goods['name'], data.get('message')))
            if data.get('code') == '-131':  # 今日已上限
                break
            await asyncio.sleep(5)

    @logger.catch
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            goods_list = await self.get_goods_list(session)
            await self.apply_for_trial(session, goods_list)


if __name__ == '__main__':
    process_start(JdTry, '京东试用')
