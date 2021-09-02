#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/21 14:32 下午
# @File    : dj_notification.py
# @Project : jd_scripts
# @Cron    : 25 10,18 * * *
# @Desc    : 京东到家活动通知
import aiohttp
import moment

from utils.console import println
from utils.process import process_start
from utils.dj_init import dj_init


@dj_init
class DjNotification:
    """
    到家APP活动通知
    """

    async def get_dj_fruit_msg(self, session):
        """
        获取到家果园信息
        """
        try:
            await self.request(session, 'userInfo/login')
            res = await self.post(session, 'fruit/initFruit', {
                "cityId": str(self.city_id), "longitude": self.lng, "latitude": self.lat})
            if res.get('code', '-1') != '0':
                return ''
            active_info = res['result']['activityInfoResponse']
            award_name = active_info['fruitName']
            stage_name = active_info['stageName']
            cur_process = round(float(active_info['curStageTotalProcess']) - float(active_info['curStageLeftProcess']),
                                2)
            total_process = active_info['curStageTotalProcess']
            if active_info['ifMaxProcess']:
                msg = f'【到家果园】{award_name}已可兑换'
            else:
                msg = f'【到家果园】{award_name}, {stage_name}进度:{cur_process}/{total_process}'

            return msg
        except:
            return ''

    async def get_bean_detail(self, session, page=1, page_size=30):
        """
        :return:
        """
        body = {
            "pageSize": page_size,
            "pageNo": page,
            "refPageSource": "Integral",
            "pageSource": "pointdetail",
            "ref": "mypoint",
            "ctp": "pointdetail"
        }
        res = await self.get(session, 'memberPoints/userPointsDetail', body)
        if res['code'] != '0':
            println('{}, 无法获取鲜豆明细!'.format(self.account))
            return None
        return res['result']

    async def get_dj_bean_manor_msg(self, session):
        """
        获取鲜豆庄园信息
        """
        try:
            res = await self.post(session, 'plantBeans/getActivityInfo')

            if res.get('code', '-1') != '0':
                return ''

            data = res.get('result', dict())
            # 上期瓜分鲜豆
            pre_bean = data.get('pre', dict()).get('points', 0)
            level = data.get('cur', dict()).get('level', 1)
            level_progress = data.get('cur', dict()).get('levelProgress', '0')
            total_progress = data.get('cur', dict()).get('totalProgress', '0')

            msg = f'【鲜豆庄园】本期等级:{level}, 本期成长值:{level_progress}/{total_progress}, 上期瓜分鲜豆:{pre_bean}'

            return msg
        except:
            return ''

    async def get_dj_bean_msg(self, session):
        """
        鲜豆变动通知
        :return:
        """
        try:
            total_bean = 0  # 鲜豆总数
            yesterday = moment.date(moment.now().sub('days', 1)).zero
            today = moment.date(moment.now()).zero
            today_used = 0  # 今日支出
            today_income = 0  # 今日收入
            yesterday_income = 0  # 昨日收入
            yesterday_used = 0  # 昨日支出

            page = 1
            finished = False

            while True:
                detail = await self.get_bean_detail(session, page)
                if not detail or 'evaluateList' not in detail or len(detail['evaluateList']) < 0:
                    break
                total_bean = detail['points']
                item_list = detail['evaluateList']
                for item in item_list:
                    day = moment.date(item['createTime'], '%H:%M:%S').zero
                    amount = int(item['points'])
                    if day.diff(yesterday).days == 0:
                        if amount > 0:  # 收入
                            yesterday_income += amount
                        else:  # 支出
                            yesterday_used += -amount

                    elif day.diff(yesterday).days >= 1:  # 昨天之前的日期跳过
                        finished = True
                        break

                    if day.diff(today).days == 0:
                        if amount > 0:
                            today_income += amount
                        else:
                            today_used = -amount
                if finished:
                    break
                else:
                    page += 1

            msg = f'【当前鲜豆总数】{total_bean}\n【今日收入鲜豆】' \
                  f'{today_income}\n【今日支出鲜豆】{today_used}\n' \
                  f'【昨日收入鲜豆】{yesterday_income}\n【昨日支出鲜豆】{yesterday_used}'

            return msg
        except:
            return ''

    async def run(self):
        """
        程序入口
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            dj_cookies = await self.login(session)
            if not dj_cookies:
                println('{}, 登录失败, 退出程序!'.format(self.account))
                return

        async with aiohttp.ClientSession(cookies=dj_cookies, headers=self.headers) as session:
            headers = '【京东账号】{}'.format(self.account)
            dj_fruit_msg = await self.get_dj_fruit_msg(session)
            dj_manor_msg = await self.get_dj_bean_manor_msg(session)
            dj_bean_msg = await self.get_dj_bean_msg(session)
            tail = '-' * 60 + '\n'

            self.message = '\n'.join([i for i in [
                headers,
                dj_bean_msg,
                dj_manor_msg,
                dj_fruit_msg,
                tail,
            ] if i])


if __name__ == '__main__':
    process_start(DjNotification, '京东到家通知')
