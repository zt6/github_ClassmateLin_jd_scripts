#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 3:10 下午
# @File    : jd_super_brand.py
# @Project : jd_scripts
# @Cron    : 30 10,22 * * *
# @Desc    : 特务Z
import asyncio
import time
import json

import aiohttp

from urllib.parse import urlencode
from config import USER_AGENT
from utils.jd_init import jd_init
from utils.console import println
from db.model import Code
from utils.process import process_start, get_code_list

# 特务Z
CODE_JD_SUPER_BRAND = 'jd_super_brand'


@jd_init
class JdSuperBrand:
    headers = {
        'user-agent': USER_AGENT,
        'referer': 'https://pro.m.jd.com/mall/active/4NwAuHsFZZfedc7NJGoVMvK2WkKD/index.html',
        'origin': 'https://pro.m.jd.com',
    }

    encrypt_project_id = None
    activity_id = None

    async def request(self, session, function_id, body=None, method='POST'):
        """
        :param session:
        :param function_id:
        :param body:
        :param method:
        :return:
        """
        try:
            if not body:
                body = {}
            params = {
                'functionId': function_id,
                'appid': 'ProductZ4Brand',
                'client': 'wh5',
                't': int(time.time() * 1000),
                'body': json.dumps(body)
            }
            url = 'https://api.m.jd.com/api?' + urlencode(params)

            if method == 'POST':
                response = await session.post(url)
            else:
                response = await session.get(url)

            text = await response.text()

            data = json.loads(text)

            if data.get('code') != '0':
                return data
            else:
                data = data['data']
                data['code'] = data.pop('bizCode')
                try:
                    data['code'] = int(data['code'])
                except:
                    pass
                data['msg'] = data.pop('bizMsg')

                return data

        except Exception as e:
            println('{}, 请求数据失败, {}!'.format(self.account, e.args))
            return {
                'code': 999,
                'msg': '请求数据失败'
            }

    async def init(self, session):
        """
        获取首页数据
        :return:
        """
        data = await self.request(session, 'superBrandSecondFloorMainPage', {"source": "secondfloor"})
        if data.get('code') != 0:
            return False
        self.encrypt_project_id = data['result']['activityBaseInfo']['encryptProjectId']
        self.activity_id = data['result']['activityBaseInfo']['activityId']
        return True

    async def do_tasks(self, session):
        """
        获取任务列表
        :param session:
        :return:
        """
        data = await self.request(session, 'superBrandTaskList', {
            "source": "secondfloor",
            "activityId": self.activity_id,
            "assistInfoFlag": 1})
        if data.get('code') != 0:
            println('{}, 获取任务列表数据失败!'.format(self.account))
            return None

        task_list = data['result']['taskList']

        for task in task_list:

            if '助力' in task['assignmentName'] or '邀请' in task['assignmentName'] :
                code_val = task['encryptAssignmentId'] + '@' + task['ext']['assistTaskDetail']['itemId']
                println('{}, 助力码:{}'.format(self.account, code_val))
                Code.insert_code(code_key=CODE_JD_SUPER_BRAND, code_val=code_val, sort=self.sort, account=self.account)
                continue

            if not task['ext']:
                item_id = 'null'
            else:
                if 'followShop' in task['ext']:
                    item_id = task['ext']['followShop'][0]['itemId']
                elif 'assistTaskDetail' in task['ext']:
                    item_id = task['ext']['assistTaskDetail']['itemId']
                elif 'brandMemberList' in task['ext']:
                    item_id = task['ext']['brandMemberList'][0]['itemId']
                else:
                    item_id = 'null'

            body = {
                "source": "secondfloor",
                "activityId": self.activity_id,
                "encryptProjectId": self.encrypt_project_id,
                "encryptAssignmentId": task['encryptAssignmentId'],
                "assignmentType": task['assignmentType'],
                "completionFlag": 1,
                "itemId": item_id,
                "actionType": 0}
            res = await self.request(session, 'superBrandDoTask', body)
            println('{}, 任务:{}, {}'.format(self.account, task['assignmentName'], res.get('msg')))

    async def help_friend(self, session):
        """
        助力好友
        :return:
        """
        item_list = Code.get_code_list(CODE_JD_SUPER_BRAND)
        item_list.extend(get_code_list(CODE_JD_SUPER_BRAND))

        for item in item_list:
            account, code = item.get('account'), item.get('code')
            if account == self.account:
                continue
            assign_id, item_id = code.split('@')
            body = {
                "source": "secondfloor",
                "activityId": self.activity_id,
                "encryptProjectId": self.encrypt_project_id,
                "encryptAssignmentId": assign_id,
                "assignmentType": 2,
                "itemId": item_id,
                "actionType": 0}
            res = await self.request(session, 'superBrandDoTask', body)

            if res.get('code') == 0:
                println('{}, 成功助力好友:{}'.format(self.account, account))
            else:
                println('{}, 无法助力好友:{}, {}'.format(self.account, account, res.get('msg')))
                if res.get('code') == 108:  # 上限
                    break

            await asyncio.sleep(1)

    async def run_help(self):
        """
        助力入口
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            if not await self.init(session):
                println('{}, 初始化失败, 退出程序!'.format(self.account))
                return
            await self.help_friend(session)

    async def lottery(self, session):
        """
        抽奖
        :return:
        """
        while True:
            res = await self.request(session, 'superBrandTaskLottery', {
                "source": "secondfloor",
                "activityId": self.activity_id})
            if res.get('code') == "TK000":
                award = res['result']['userAwardInfo']
                if not award:
                    award = '无'
                elif award.get('awardType') == 3:
                    award = '{}京豆'.format(award['beanNum'])
                println('{}, 抽奖成功, 获得:{}'.format(self.account, award))
            else:
                break
            await asyncio.sleep(1)

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            if not await self.init(session):
                println('{}, 初始化失败, 退出程序!'.format(self.account))
                return
            await self.do_tasks(session)
            await self.lottery(session)


if __name__ == '__main__':
    process_start(JdSuperBrand, '特物Z')
