#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/28 9:35 上午
# @File    : jd_lottery_bean.py
# @Project : jd_scripts
# @Cron    : 6 0 * * *
# @Desc    : 京东APP->签到领京豆->抽京豆
import aiohttp
import json
from utils.console import println
from utils.jd_init import jd_init
from utils.process import process_start


@jd_init
class JdLotteryBean:
    """
    抽京豆
    """
    headers = {
        'referer': 'https://turntable.m.jd.com',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    async def lottery(self, session):
        """
        抽京豆
        :param session:
        :return:
        """
        url = 'https://api.m.jd.com/client.action?functionId=babelGetLottery&clientVersion=10.1.2&build=89743&client' \
              '=android&oaid=&openudid=a27b83d3d1dba1cc&uuid=a27b83d3d1dba1cc&aid=a27b83d3d1dba1cc&networkType=wifi' \
              '&uemps=0-0&harmonyOs=0&st=1630686786705&sign=be9521d4f903167e3e01074d8f8b6823&sv=101'
        body = 'body=%7B%22authType%22%3A%222%22%2C%22awardSource%22%3A%221%22%2C%22enAwardK%22%3A' \
               '%22d4afa87576d7256be7f93705f3ac4ac6%22%2C%22encryptAssignmentId%22%3A%224LxnGaaLFvTy5d7jPUvqbVg39vu8' \
               '%22%2C%22encryptProjectId%22%3A%22qNaNGnukN44Ka4pu1LqRkEieywh%22%2C%22lotteryCode%22%3A%22153871%22' \
               '%2C%22riskParam%22%3A%7B%22childActivityUrl%22%3A%22https%3A%2F%2Fpro.m.jd.com%2Fmall%2Factive' \
               '%2FeZPwLvs4bH5LRkbdm3vLBv76FHH%2Findex.html%3Ftttparams' \
               '%3Dwc55025fHeyJnTGF0IjoiMjMuMDEzMTAxIiwiZ0xuZyI6IjExMy4zOTAwNTEifQ9%253D%253D%22%2C%22eid%22%3A' \
               '%22eidA032a81222asaKrq38pv1Smu4CcoLNmssuSq6uW5IaTgOUxBHdNSLeAQhYJKsAr1ni1FkoE84A3b0R3nbznVBN0H3IoNwfB' \
               '%2FfhJJsi5KY4w5KFphi%22%2C%22pageClickKey%22%3A%22Babel_WheelSurf%22%2C%22shshshfpb%22%3A%22zyIEXXcEj' \
               '%2Bo%2FT7BgWolC5HlcQo72LyOIHBAzbP9RRfNACqMJteLVdK1iEgWcDupTqDWucyE3D5VfGTptpZEJCqw%3D%3D%22%7D%7D& '
        try:
            response = await session.post(url=url, data=body)
            text = await response.text()
            data = json.loads(text)

            if data.get("code") != "0":
                println('{}, 抽京豆失败!'.format(self.account))
                return

            println('{}, 抽奖结果:{}, 获得奖励:{}'.format(self.account, data.get('promptMsg', '未知'), data.get('prizeName', '无')))

        except Exception as e:
            println('{}, 抽京豆错误!{}'.format(self.account, e.args))

    async def run(self):
        """
        程序入口
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            await self.lottery(session)


if __name__ == '__main__':
    process_start(JdLotteryBean, '抽京豆')
