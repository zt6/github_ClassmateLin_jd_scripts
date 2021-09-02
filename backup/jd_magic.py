#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/15 上午11:16
# @Project : jd_scripts
# @File    : jd_magic.py
# @Cron    : 37 3,12 * * *
# @Desc    :
from utils.jd_common import JdCommon
from config import USER_AGENT

CODE_KEY = 'jd_magic'


class JdMagic(JdCommon):
    """
    """
    code_key = CODE_KEY

    appid = "1E1NYwqc"

    # 请求头
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://h5.m.jd.com/babelDiy/Zeus/3RejAk5YXzhvxXiBR1tzWnUbwneW/index.html',
        'User-Agent': USER_AGENT
    }


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdMagic, '荣耀换新季', code_key=CODE_KEY)
