#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/8 11:38 上午
# @File    : jd_bean_change.py
# @Project : jd_scripts
# @Cron    : 15 */8 * * *
# @Desc    : 京豆红包变动通知
import aiohttp
import asyncio
import json
import moment
import time

from urllib.parse import quote

from utils.logger import logger
from utils.console import println
from utils.jd_init import jd_init

from config import USER_AGENT


@jd_init
class JdBeanChange:
    """
    资产变动通知
    """
    headers = {
        'Host': 'api.m.jd.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': USER_AGENT,
    }

    async def get_bean_detail(self, session, page=1, timeout=0.5):
        """
        获取京豆详情页数据
        :param timeout:
        :param page:
        :param session:
        :return:
        """
        try:
            session.headers.add('Host', 'api.m.jd.com')
            session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
            await asyncio.sleep(timeout)
            url = 'https://api.m.jd.com/client.action?functionId=getJingBeanBalanceDetail'
            body = 'body={}&appid=ld'.format(quote(json.dumps({"pageSize": "20", "page": str(page)})))
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)
            return data['detailList']
        except Exception as e:
            println('{}, 获取服务器数据失败, {}!'.format(self.account, e.args))
            return []

    async def get_expire_bean(self, session, timeout=0.5):
        """
        :param timeout:
        :param session:
        :return:
        """
        try:
            println('{}, 正在获取即将过期京豆数据...'.format(self.account, timeout))
            await asyncio.sleep(timeout)
            session.headers.add('Referer', 'https://wqs.jd.com/promote/201801/bean/mybean.html')
            session.headers.add('Host', 'wq.jd.com')
            session.headers.add('Content-Type', 'application/x-www-form-urlencoded')
            url = 'https://wq.jd.com/activep3/singjd/queryexpirejingdou?_={}&g_login_type=1&sceneval=2'.\
                format(int(time.time()*1000))
            response = await session.get(url=url)
            text = await response.text()
            data = json.loads(text[23:-13])
            res = []

            for item in data['expirejingdou']:
                amount = item['expireamount']
                if amount == 0:
                    continue
                msg = '【{}即将过期京豆】:{}'.format(moment.unix(item['time']).zero.format('YYYY-M-D'), amount)
                res.append(msg)
            return res
        except Exception as e:
            println('{}, 获取即将过期的京豆数据失败:{}.'.format(self.account, e.args))
            return []

    async def total_bean(self, session):
        """
        京豆统计
        :param session:
        :return:
        """
        bean_amount = await self.get_bean_amount(session)  # 当前总京豆
        expire_record = await self.get_expire_bean(session)  # 获取过期京豆数据
        today_income = 0   # 今日收入
        today_used = 0   # 今日支出
        yesterday_income = 0  # 昨日收入
        yesterday_used = 0  # 昨日支出
        yesterday = moment.date(moment.now().sub('days', 1)).zero
        today = moment.date(moment.now()).zero
        page = 1
        finished = False

        println('{}, 正在获取京豆明细...'.format(self.account))
        while True:
            detail_list = await self.get_bean_detail(session, page)
            if len(detail_list) < 1:
                break
            for item in detail_list:
                day = moment.date(item['date'], '%H:%M:%S').zero
                amount = int(item['amount'])
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
            page += 1

            if finished:
                break

        return {
            'bean_amount': bean_amount,
            'today_income': today_income,
            'today_used': today_used,
            'yesterday_income': yesterday_income,
            'yesterday_used': yesterday_used,
            'expire': expire_record
        }

    async def get_bean_amount(self, session, timeout=0.5):
        """
        获取当前京豆总数
        :param timeout:
        :param session:
        :return:
        """
        try:
            println('{}, 正在获取京豆总数...'.format(self.account, timeout))
            await asyncio.sleep(timeout)
            url = 'https://me-api.jd.com/user_new/info/GetJDUserInfoUnion'
            session.headers.add('Host', 'me-api.jd.com')
            session.headers.add('Referer', 'https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&')
            response = await session.get(url)
            text = await response.text()
            data = json.loads(text)
            if data['retcode'] == '0' and 'data' in data and 'assetInfo' in data['data']:
                return int(data['data']['assetInfo']['beanNum'])
            else:
                return 0
        except Exception as e:
            println('{}, 获取京豆总数失败:{}!'.format(self.account, e.args))
            return 0

    async def total_red_packet(self, session):
        """
        统计红包
        :param session:
        :return:
        """
        res = {
            'total_amount': 0,
            'expire_amount': 0,
        }
        try:
            session.headers.add('Referer', 'https://st.jingxi.com/my/redpacket.shtml?newPg=App&jxsid'
                                           '=16156262265849285961')
            session.headers.add('Host', 'm.jingxi.com')

            url = 'https://m.jingxi.com/user/info/QueryUserRedEnvelopesV2?type=1&orgFlag=JD_PinGou_New&page=1' \
                  '&cashRedType=1&redBalanceFlag=1&channel=1&_={}' \
                  '&sceneval=2&g_login_type=1&g_ty=ls'.format(int(time.time() * 1000))

            response = await session.get(url=url)
            text = await response.text()
            data = json.loads(text)
            if data['errcode'] != 0:
                return res
            res['total_amount'] = data['data']['balance'].strip()
            res['expire_amount'] = data['data']['expiredBalance'].strip()
            return res

        except Exception as e:
            println('{}, 获取红包数据失败:{}!'.format(self.account, e.args))
            return res

    async def notify(self, session):
        """
        设置消息通知
        :param session:
        :return:
        """
        bean_data = await self.total_bean(session)  # 京豆统计数据
        red_packet_data = await self.total_red_packet(session)  # 红包统计数据

        message = '【京东账号】{}\n'.format(self.account)
        message += '【京豆总数】{}\n'.format(bean_data['bean_amount'])
        message += '【今日收入】{}京豆\n'.format(bean_data['today_income'])
        message += '【今日支出】{}京豆\n'.format(bean_data['today_used'])
        message += '【昨日收入】{}京豆\n'.format(bean_data['yesterday_income'])
        message += '【昨日支出】{}京豆\n'.format(bean_data['yesterday_used'])
        for item in bean_data['expire']:
            message += item + '\n'
        message += '【当前红包余额】{}￥\n'.format(red_packet_data['total_amount'])
        message += '【即将过期红包】{}￥\n'.format(red_packet_data['expire_amount'])
        self.message = message

    async def run(self):
        """
        程序入库
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            await self.notify(session)


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdBeanChange, '资产变动通知')
