#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/23 下午1:27
# @Project : jd_scripts
# @File    : jd_carnival_city.py
# @Cron    : 1 1 * * *
# @Desc    : 京东APP首页->手机->手机嗨购日->一亿京豆悬浮窗
import asyncio
import json
import time
import urllib.parse

import aiohttp

from config import USER_AGENT
from utils.process import process_start, get_code_list
from utils.console import println
from utils.jd_init import jd_init
from utils.logger import logger
from db.model import Code

# 手机狂欢城
CODE_JD_CARNIVAL_CITY = 'jd_carnival_city'


@jd_init
class JdCarnivalCity:
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': USER_AGENT,
        'referer': 'https://carnivalcity.m.jd.com/'
    }

    @logger.catch
    async def request(self, session, function_id, body=None, method='POST'):
        """
        请求数据
        :param session:
        :param function_id:
        :param body:
        :param method:
        :return:
        """
        try:
            if not body:
                body = {}
            url = 'https://api.m.jd.com/api'
            params = {
                'appid': 'guardian-starjd',
                't': int(time.time() * 1000),
                'loginType': '2',
                'body': json.dumps(body),
                'functionId': function_id,
            }
            url += '?' + urllib.parse.urlencode(params)
            if method == 'POST':
                response = await session.post(url=url)
            else:
                response = await session.get(url=url)

            text = await response.text()
            data = json.loads(text)
            return data
        except Exception as e:
            println('{}, 请求服务器数据失败, {}!'.format(self.account, e.args))
            return {
                'code': -9999
            }

    @logger.catch
    async def do_browse_task(self, session, body, brand_id=''):
        """
        做任务
        :param brand_id:
        :param body:
        :param session:
        :param task:
        :return:
        """
        res = await self.request(session, 'carnivalcity_jd_prod', body)
        browser_id = res.get('data', dict()).get('browseId')
        if not browser_id:
            return
        println('{}, 正在浏览任务:{}, 需要等待6s!'.format(self.account, browser_id))
        await asyncio.sleep(6)
        body = {"brandId": brand_id,
                "browseId": browser_id,
                "apiMapping": "/khc/task/getBrowsePrize"}
        await self.request(session, 'carnivalcity_jd_prod', body)

    @logger.catch
    async def do_host_product_tasks(self, session, task_list):
        """
        做热销产品任务
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            if task['status'] == '4':
                continue
            body = {"brandId": "", "id": task['id'], "taskMark": "hot", "type": "browse", "logMark": "browseHotSku",
                    "apiMapping": "/khc/task/doBrowse"}
            await self.do_browse_task(session, body)

    @logger.catch
    async def get_brand_info(self, session, brand_id):
        """
        获取品牌明细
        :param session:
        :param brand_id:
        :return:
        """
        body = {"brandId": brand_id, "apiMapping": "/khc/index/brandTaskInfo"}
        res = await self.request(session, 'carnivalcity_jd_prod', body)
        return res.get('data', dict())

    @logger.catch
    async def do_brand_sku_tasks(self, session, brand_id, task_list):
        """
        做品牌任务的sku任务
        :param brand_id:
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            body = {"brandId": brand_id, "id": task['id'], "taskMark": "brand", "type": "presell",
                    "logMark": "browseSku", "apiMapping": "/khc/task/doBrowse"}
            await self.do_browse_task(session, body, brand_id=brand_id)

    @logger.catch
    async def do_brand_meeting_tasks(self, session, brand_id, task_list):
        """
        品牌任务下的会场任务
        :param brand_id:
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            body = {"brandId": brand_id, "id": task['id'], "taskMark": "brand", "type": "meeting",
                    "logMark": "browseVenue", "apiMapping": "/khc/task/doBrowse"}
            await self.do_browse_task(session, body, brand_id=brand_id)

    @logger.catch
    async def do_brand_task(self, session, task_list):
        """
        做品牌任务
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            if task['status'] == '4':
                continue
            data = await self.get_brand_info(session, task['brandId'])
            sku_tasks = data.get('skuTask', [])
            shop_task = data.get('shopTask', dict())
            if shop_task:
                body = {"id": shop_task[0]['id'], "brandId": task['brandId'], "apiMapping": "/khc/task/followShop"}
                await self.request(session, 'carnivalcity_jd_prod', body)
                await asyncio.sleep(1)
            await self.do_brand_sku_tasks(session, task['brandId'], sku_tasks)  # 2F 逛商品
            meeting_tasks = data.get('meetingTask', [])
            await self.do_brand_meeting_tasks(session, task['brandId'], meeting_tasks)

            question_task = data.get('questionTask', dict())
            if not question_task:
                continue
            answers_id = 1
            for i in range(len(question_task['answers'])):
                if question_task['answers'][i]['right']:
                    answers_id = i + 1
            body = {"brandId": task['brandId'], "questionId": question_task['id'],
                    "result": answers_id, "apiMapping": "/khc/task/doQuestion"}
            await self.request(session, 'carnivalcity_jd_prod', body)
            await asyncio.sleep(1)

    @logger.catch
    async def do_browse_shop_task(self, session, task_list):
        """
        逛好货街任务
        :param session:
        :param task_list:
        :return:
        """
        for task in task_list:
            if task['status'] != '6':
                continue
            body = {"brandId": "", "id": task['id'], "taskMark": "browseShop", "type": "browse",
                    "logMark": "secondBlock", "apiMapping": "/khc/task/doBrowse"}
            await self.do_browse_task(session, body)

    @logger.catch
    async def do_tasks(self, session):
        """
        做任务
        :param session:
        :return:
        """
        res = await self.request(session, 'carnivalcity_jd_prod', {"apiMapping": "/khc/index/indexInfo"})
        if res.get('code') != 200:
            println('{}, 获取任务列表失败'.format(self.account))
            return

        data = res['data']

        hot_product_list = data['hotProductList']
        brand_list = data['brandList']
        browse_shop_list = data['browseshopList']

        await self.do_host_product_tasks(session, hot_product_list)
        await self.do_brand_task(session, brand_list)
        await self.do_browse_shop_task(session, browse_shop_list)

    @logger.catch
    async def get_share_code(self, session):
        """
        获取助力码
        :return:
        """
        body = {"apiMapping": "/khc/task/getSupport"}
        res = await self.request(session, 'carnivalcity_jd_prod', body)
        if res.get('code') != 200:
            println('{}, 无法获取助力码!'.format(self.account))
            return
        share_code = res.get('data', dict()).get('shareId')
        Code.insert_code(code_key=CODE_JD_CARNIVAL_CITY, code_val=share_code, sort=self.sort, account=self.account)
        println('{}, 助力码:{}'.format(self.account, share_code))

    @logger.catch
    async def lottery(self, session):
        """
        抽奖
        :param session:
        :return:
        """
        while True:
            body = {"apiMapping": "/khc/record/lottery"}
            res = await self.request(session, 'carnivalcity_jd_prod', body)
            if res.get('code') != 200:
                println('{}, 积分已不够抽奖!'.format(self.account))
                break
            println('{}, 抽奖结果:{}'.format(self.account, res.get('data', dict()).get('prizeName', '未知')))
            await asyncio.sleep(1)

    @logger.catch
    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.get_share_code(session)
            await self.do_tasks(session)
            await self.lottery(session)

    @logger.catch
    async def run_help(self):
        """
        助力好友
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            item_list = Code.get_code_list(code_key=CODE_JD_CARNIVAL_CITY)
            item_list.extend(get_code_list(CODE_JD_CARNIVAL_CITY))

            for item in item_list:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue
                body = {
                    "shareId": code,
                    "apiMapping": "/khc/task/doSupport"}
                res = await self.request(session, 'carnivalcity_jd_prod', body)
                println('{}, 助力好友:{}, 结果:{}'.format(self.account, account, res.get('msg', '未知')))


if __name__ == '__main__':
    process_start(JdCarnivalCity, '手机狂欢城', code_key=CODE_JD_CARNIVAL_CITY)
