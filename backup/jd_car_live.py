#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/15 上午11:47
# @Project : jd_scripts
# @File    : jd_car_live.py
# @Cron    : 22 4,17 * * *
# @Desc    : 汽车生活节
from utils.jd_common import JdCommon
from config import USER_AGENT

CODE_KEY = 'jd_car_live'


class JdCarLive(JdCommon):
    """
    """
    code_key = CODE_KEY

    appid = "1E1xRy6c"

    # 请求头
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://h5.m.jd.com/babelDiy/Zeus/2FdCyR9rffxKUkMpQTP4WT4bArmL/index.html',
        'User-Agent': USER_AGENT
    }


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdCarLive, '汽车生活节', code_key=CODE_KEY)

    # from config import JD_COOKIES
    # import asyncio
    # app = JdCarLive(**JD_COOKIES[0])
    # asyncio.run(app.run())