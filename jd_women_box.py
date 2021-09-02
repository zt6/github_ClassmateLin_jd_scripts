#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/27 10:00 上午
# @File    : jd_women_box.py
# @Project : jd_scripts
# @Cron    : 5 1 * * *
# @Desc    : 女装盲盒
from utils.jd_anmp import JdAnmp
from utils.process import process_start


class JdWomenBox(JdAnmp):
    """
    女装盲盒
    """
    url = 'https://anmp.jd.com/babelDiy/Zeus/3bMo2AgbRYYfZt83qHLZ3ruVtrtG/index.html'


if __name__ == '__main__':
    process_start(JdWomenBox, '女装盲盒')
