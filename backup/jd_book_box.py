#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/9/7 2:29 下午
# @File    : jd_book_box.py
# @Cron    : 50 12 * * *
# @Project : jd_scripts
# @Desc    :
from utils.jd_anmp import JdAnmp
from utils.process import process_start


class JdBookBox(JdAnmp):
    """
    开学图书盲盒
    """
    url = 'https://h5.m.jd.com/babelDiy/Zeus/3tcmvheLZSeuP349ci3KTS7szJaS/'


if __name__ == '__main__':
    process_start(JdBookBox, '开学图书盲盒')


