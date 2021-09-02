#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/13 1:58 下午
# @File    : jd_gold_creator.py
# @Project : jd_scripts
# @Cron    : 30 7,19 * * *
# @Desc    : 京东APP->排行榜->金榜创造营
import asyncio
import aiohttp
import json
import re
import random

from urllib.parse import unquote, quote
from config import USER_AGENT
from utils.console import println
from utils.jd_init import jd_init


@jd_init
class JdGoldCreator:

    headers = {
        'referer': 'https://h5.m.jd.com/babelDiy/Zeus/2H5Ng86mUJLXToEo57qWkJkjFPxw/index.html',
        'user-agent': USER_AGENT,
    }

    async def request(self, session, function_id, body=None):
        try:
            if body is None:
                body = {}
            url = 'https://api.m.jd.com/client.action?functionId={}&body={}' \
                  '&appid=content_ecology&clientVersion=10.0.6&client=wh5' \
                  '&jsonp=jsonp_kr1mdm3p_12m_29&eufv=false'.format(function_id, quote(json.dumps(body)))
            response = await session.post(url=url)
            text = await response.text()
            temp = re.search(r'\((.*)\);', text).group(1)
            data = json.loads(temp)
            await asyncio.sleep(3)
            return data
        except Exception as e:
            println('{}, 获取数据失败:{}'.format(self.account, e.args))
            return None

    async def get_index_data(self, session):
        """
        获取获得首页数据
        :param session:
        :return:
        """
        return await self.request(session, 'goldCreatorTab', {"subTitleId": "", "isPrivateVote": "0"})

    async def do_vote(self, session):
        """
        进行投票
        :param session:
        :param index_data:
        :return:
        """
        println('{}, 正在获取投票主题...'.format(self.account))
        data = await self.get_index_data(session)
        if not data or data['code'] != '0':
            println('{}, 获取数据失败!'.format(self.account))
            return
        subject_list = data['result']['subTitleInfos']
        stage_id = data['result']['mainTitleHeadInfo']['stageId']
        for subject in subject_list:
            if 'taskId' not in subject:
                continue
            body = {
                "groupId": subject['matGrpId'],
                "stageId": stage_id,
                "subTitleId": subject['subTitleId'],
                "batchId": subject['batchId'],
                "skuId": "",
                "taskId": int(subject['taskId']),
            }
            res = await self.request(session, 'goldCreatorDetail', body)
            if res['code'] != '0':
                println('{}, 获取主题:《{}》商品列表失败!'.format(self.account, subject['shortTitle']))
            else:
                println('{}, 获取主题:《{}》商品列表成功, 开始投票!'.format(self.account, subject['shortTitle']))

            await asyncio.sleep(2)

            task_list = res['result']['taskList']
            sku_list = res['result']['skuList']
            item_id = res['result']['signTask']['taskItemInfo']['itemId']
            sku = random.choice(sku_list)
            body = {
                "stageId": stage_id,
                "subTitleId": subject['subTitleId'],
                "skuId": sku['skuId'],
                "taskId": int(subject['taskId']),
                "itemId": item_id,
                "rankId": sku["rankId"],
                "type": 1,
                "batchId": subject['batchId'],
            }
            res = await self.request(session, 'goldCreatorDoTask', body)

            if res['code'] != '0':
                println('{}, 为商品:《{}》投票失败!'.format(self.account, sku['name']))
            else:
                if 'lotteryCode' in res['result'] and res['result']['lotteryCode'] != '0':
                    println('{}, 为商品:《{}》投票失败, {}'.format(self.account, sku['name'], res['result']['lotteryMsg']))
                elif 'taskCode' in res['result'] and res['result']['taskCode'] == '103':
                    println('{}, 为商品: 《{}》投票失败, {}!'.format(self.account, sku['name'], res['result']['taskMsg']))
                else:
                    println('{}, 为商品:《{}》投票成功, 获得京豆:{}'.format(self.account, sku['name'], res['result']['lotteryScore']))

            for task in task_list:
                if task[0]['taskStatus'] == 2:
                    continue
                body = {
                    "taskId": int(task[0]['taskId']),
                    "itemId": task[0]['taskItemInfo']['itemId'],
                    "type": 2,
                    "batchId": subject['batchId']
                }
                res = await self.request(session, 'goldCreatorDoTask', body)

                println('{}, 做额外任务: 《{}》, 结果:{}!'.format(self.account, task[0]['taskItemInfo']['title'], res))

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            await self.do_vote(session)  # 投票


if __name__ == '__main__':

    from utils.process import process_start
    process_start(JdGoldCreator, '金榜创造营')
