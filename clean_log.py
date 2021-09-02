#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/21 2:01 下午
# @File    : clean_log.py
# @Project : jd_scripts
# @Cron    : 30 23 * * *
# @Desc    : 清除日志, 默认保留三天, 可在配置中修改
import re
import os
import moment
from config import LOG_DIR
from utils.console import println


def clean_log(days=2):
    """
    清除日志
    :param days: 保留n天的日志
    :return:
    """
    count = 0
    prev_date = moment.now().sub(days=days)
    for file in os.listdir(LOG_DIR):
        if os.path.splitext(file)[-1] != '.log':   # 跳过非日志文件
            continue
        try:
            date = moment.date(re.split(r'\.|_', file)[-2])
            if date < prev_date:
                os.remove(os.path.join(LOG_DIR, file))
                count += 1
        except Exception as e:
            println(e.args)
    println('成功清除个{}日志文件!'.format(count))


if __name__ == '__main__':
    clean_log()
