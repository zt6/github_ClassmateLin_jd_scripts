#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/7 21:48
# @File    : jd_wishing_pool.py
# @Project : jd_scripts
# @Cron    : 45 */12 * * *
# @Desc    : 京东APP首页->京东众筹->众筹许愿池

from utils.jd_common import JdCommon
from config import USER_AGENT

CODE_KEY = 'jd_wishing_pool'


class JdWishingPool(JdCommon):
    """
    众筹许愿池
    """
    appid = '1E1NXxq0'

    code_key = CODE_KEY

    # 请求头
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://h5.m.jd.com/babelDiy/Zeus/4FdmTJQNah9oDJyQN8NggvRi1nEY/index.html',
        'User-Agent': USER_AGENT
    }


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdWishingPool, '众筹许愿池', code_key=CODE_KEY)
