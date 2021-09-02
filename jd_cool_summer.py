#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/26 11:18 上午
# @File    : jd_cool_summer.py
# @Project : jd_scripts
# @Cron    : 8 8 * * *
# @Desc    : 清凉一夏
from utils.jd_anmp import JdAnmp
from utils.process import process_start


class JdCoolSummer(JdAnmp):
    """
    清凉一夏
    """
    url = 'https://anmp.jd.com/babelDiy/Zeus/3pG9h6Buegznv8rhVMzMR753pUtY/index.html'


if __name__ == '__main__':
    process_start(JdCoolSummer, '清凉一夏')
