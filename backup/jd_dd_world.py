#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/22 11:49 上午
# @File    : jd_dd_world.py
# @Project : jd_scripts
# @Cron    : 2 8,13 * * *
# @Desc    : 东东世界
import asyncio
import json
import aiohttp
from urllib.parse import quote
from utils.console import println
from utils.jd_init import jd_init
from utils.logger import logger
from config import USER_AGENT
from db.model import Code

CODE_KEY = 'dd_world'


@jd_init
class JdDdWorld:
    """
    东东世界
    """

    @logger.catch
    async def get_isv_token_key(self):
        """
        获取isv token
        :return:
        """
        try:
            headers = {
                'Host': 'api.m.jd.com',
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'referer': '',
                'user-agent': 'JD4iPhone/167814 (iPhone; iOS 12.4.1; Scale/3.00)',
                'accept-language': 'zh-Hans-CN;q=1',
            }
            async with aiohttp.ClientSession(headers=headers, cookies=self.cookies) as session:
                url = 'https://api.m.jd.com/client.action?functionId=genToken'
                body = 'body=%7B%22to%22%3A%22https%3A%2F%2Fddsj-dz.isvjcloud.com%2Fdd-world%2Fload_app%2Fload_app.html' \
                       '%22%2C%22action%22%3A%22to%22%7D&uuid=4ccb375c539fd92bade&client=apple&clientVersion=10.0.10&st' \
                       '=1631884082694&sv=111&sign=1a49fd69e7d3c18cad91cc00ed40d327'
                response = await session.post(url=url, data=body)

                text = await response.text()

                data = json.loads(text)

                return data['tokenKey']
        except:
            return None

    @logger.catch
    async def get_isv_token(self):
        """
        :param isv_token:
        :return:
        """
        try:
            headers = {
                'Host': 'api.m.jd.com',
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded',
                'referer': '',
                'user-agent': 'JD4iPhone/167814 (iPhone; iOS 12.4.1; Scale/3.00)',
                'accept-language': 'zh-Hans-CN;q=1',
            }
            async with aiohttp.ClientSession(cookies=self.cookies, headers=headers) as session:
                url = 'https://api.m.jd.com/client.action?functionId=isvObfuscator'
                body = 'body=%7B%22id%22%3A%22%22%2C%22url%22%3A%22https%3A%2F%2Fddsj-dz.isvjcloud.com%22%7D&uuid' \
                       '=5162ca82aed35fc52e8&client=apple&clientVersion=10.0.10&st=1631884203742&sv=112&sign' \
                       '=fd40dc1c65d20881d92afe96c4aec3d0'
                response = await session.post(url=url, data=body)

                text = await response.text()

                data = json.loads(text)

                return data['token']
        except:
            return None

    @logger.catch
    async def get_access_token(self, isv_token_key, isv_token):
        """
        获取access token
        :param isv_token_key:
        :param isv_token:
        :return:
        """
        try:
            headers = {
                'Host': 'ddsj-dz.isvjcloud.com',
                'Origin': 'https://ddsj-dz.isvjcloud.com',
                'Authorization': 'Bearer undefined',
                'User-Agent': USER_AGENT,
                'content-type': 'application/x-www-form-urlencoded',
                'Referer': 'https://ddsj-dz.isvjcloud.com',
                'Cookie': f'IsvToken={isv_token_key};'
            }
            async with aiohttp.ClientSession(cookies=self.cookies, headers=headers) as session:
                url = 'https://ddsj-dz.isvjcloud.com/dd-api/jd-user-info'
                body = 'token={}&source=01'.format(isv_token)

                response = await session.post(url=url, data=body)

                text = await response.text()
                # status_code
                data = json.loads(text)

                if 'status_code' in data:
                    return None
                return data['access_token']
        except:
            return None

    @logger.catch
    async def request(self, session, fn, body=''):
        """
        请求数据
        :param session:
        :param fn:
        :param body:
        :return:
        """
        try:
            url = 'https://ddsj-dz.isvjcloud.com/dd-api/{}'.format(fn)
            if body:
                response = await session.post(url=url, data=body)
            else:
                response = await session.get(url)

            text = await response.text()

            data = json.loads(text)

            return data

        except Exception as e:
            println('{}, 请求服务器数据失败, {}'.format(self.account, e.args))

    @logger.catch
    async def get_headers(self):
        """
        获取请求头
        :return:
        """
        isv_token_key = await self.get_isv_token_key()
        if not isv_token_key:
            println('{}, 无法获取isv_token_key, 退出程序...'.format(self.account))
            return

        isv_token = await self.get_isv_token()
        if not isv_token:
            println('{}, 无法获取isv_token2, 退出程序...'.format(self.account))
            return

        access_token = await self.get_access_token(isv_token_key, isv_token)
        if not access_token:
            println('{}, 无法获取access_token, 退出程序...'.format(self.account))

        headers = {
            'Host': 'ddsj-dz.isvjcloud.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': USER_AGENT,
            'Authorization': f'Bearer {access_token}',
            'Referer': 'https://ddsj-dz.isvjcloud.com/dd-world/',
        }
        return headers

    @logger.catch
    async def do_tasks(self, session):
        """
        做任务
        :return:
        """
        res = await self.request(session, 'get_task')

        if res.get('bizCode', '-1') != '0':
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        task_list = res.get('result', dict()).get('taskVos', list())

        for task in task_list:

            if task['status'] == 2:
                println('{}, 任务:《{}》今日已完成!'.format(self.account, task['taskName']))
                continue
            if 'simpleRecordInfoVo' in task:  # 签到任务
                body = 'taskToken={}&task_id={}&task_type={}'.format(task['simpleRecordInfoVo']['taskToken'],
                                                                     task['taskId'], task['taskType'])
                res = await self.request(session, 'do_task', body)

                println('{}, 签到成功, 获得金币:{}'.format(self.account, res.get('score', '0')))
                await asyncio.sleep(1)
                continue

            if task['taskType'] == 6:  # 好友助力
                res = await self.request(session, 'get_user_info')
                code = json.dumps({
                    'taskToken': task['assistTaskDetailVo']['taskToken'],
                    'inviter_id': res.get('openid', '')
                })
                println('{}, 助力码: {}'.format(self.account, code))
                Code.insert_code(code_key=CODE_KEY, code_val=code, account=self.account, sort=self.sort)
                continue

            item_list = task.get('browseShopVo') or task.get('shoppingActivityVos', []) \
                        or task.get('productInfoVos', [])

            for item in item_list:
                if item['status'] == 2:
                    continue
                task_type = task['taskType']
                task_token = item['taskToken']
                task_id = task['taskId']
                task_name = item.get('shopName', '') or item.get('title', '') or item.get('skuName', '')
                body = 'taskToken={}&task_id={}&task_type={}task_name={}'.format(task_token, task_id, task_type,
                                                                                 quote(task_name))
                res = await self.request(session, 'do_task', body)
                println('{}, 完成任务, {}'.format(self.account, res))
                await asyncio.sleep(1)

    async def run(self):
        """
        程序入口
        :return:
        """
        headers = await self.get_headers()
        async with aiohttp.ClientSession(headers=headers, cookies=self.cookies) as session:
            await self.do_tasks(session)

    @logger.catch
    async def run_help(self):
        """
        助力入口
        :return:
        """
        headers = await self.get_headers()
        async with aiohttp.ClientSession(headers=headers, cookies=self.cookies) as session:
            item_list = Code.get_code_list(CODE_KEY)
            for item in item_list:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue
                code = json.loads(code)
                body = 'taskToken={}&inviter_id={}'.format(code['taskToken'], code['inviter_id'])
                res = await self.request(session, 'do_assist_task', body)
                msg = res.get('message', '成功')
                println('{}, 助力好友:{}, 结果:{}'.format(self.account, account, msg))

                if '用完' in msg:
                    break

                await asyncio.sleep(1)


if __name__ == '__main__':
    # from config import JD_COOKIES
    #
    # app = JdDdWorld(**JD_COOKIES[0])
    # asyncio.run(app.run_help())
    from utils.process import process_start
    process_start(JdDdWorld, '东东世界', code_key=CODE_KEY)
