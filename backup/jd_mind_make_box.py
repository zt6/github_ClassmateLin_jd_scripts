#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/17 5:37 下午
# @File    : jd_mind_make_box.py
# @Project : jd_scripts
# @Cron    : 22 3,10 15-23 * *
# @Desc    : 京东app->我的->签到领豆->边玩边赚->企有此礼

from utils.jd_common import JdCommon

CODE_KEY = 'jd_mind_make_box'


class JdMindMakeBox(JdCommon):
    """
    芯意制造盒
    """
    code_key = CODE_KEY

    appid = "1ElJYxqY"


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JdMindMakeBox, '芯意制造盒', code_key=CODE_KEY)
