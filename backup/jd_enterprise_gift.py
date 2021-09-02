#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/17 5:32 下午
# @File    : jd_enterprise_gift.py
# @Project : jd_scripts
# @Cron    : 40 8,22 15-30 * *
# @Desc    : 京东app->我的->签到领豆->边玩边赚->企有此礼

from utils.jd_common import JdCommon

CODE_KEY = 'jd_enterprise_gift'


class JdEnterpriseGift(JdCommon):
    """
    """
    code_key = CODE_KEY

    appid = "1ElBTx6o"


# 1ElJYxqY
if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdEnterpriseGift, '企有此礼', code_key=CODE_KEY)
