#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/21 上午11:15
# @Project : jd_scripts
# @File    : jd_school_charging.py
# @Cron    : 1 3 * * *
# @Desc    : 京东APP->我的->签到领豆->边玩边赚->开学充电站
from utils.jd_common import JdCommon
from config import USER_AGENT

CODE_KEY = 'jd_school_charging'


class JdSchoolCharging(JdCommon):
    """
    """
    code_key = CODE_KEY

    appid = "1E1xVyqw"

    # 请求头
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://h5.m.jd.com/babelDiy/Zeus/2FdCyR9rffxKUkMpQTP4WT4bArmL/index.html',
        'User-Agent': USER_AGENT
    }


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdSchoolCharging, '开学充电站', code_key=CODE_KEY)
