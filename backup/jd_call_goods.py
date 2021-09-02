#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/15 下午12:16
# @Project : jd_scripts
# @File    : jd_call_goods.py
# @Cron    : 44 1,19 * * *
# @Desc    : 京东APP->我的->签到领豆->边玩边赚->来电好物季
from utils.jd_common import JdCommon
from config import USER_AGENT

CODE_KEY = 'jd_call_goods'


class JdCallGoods(JdCommon):
    """
    """
    code_key = CODE_KEY

    appid = "1E1NYw6w"

    # 请求头
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://h5.m.jd.com/babelDiy/Zeus/4BvJGuWhUZkGTF9Z2FryWtrLWbDm/index.html',
        'User-Agent': USER_AGENT
    }


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdCallGoods, '来电好物季', code_key=CODE_KEY)

