#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/29 1:19 下午
# @File    : model.py
# @Project : jd_scripts
# @Desc    : model定义
import hashlib
import os
import random
import time

import urllib3
from datetime import datetime
from functools import reduce

import requests
from peewee import *
from config import DB_PATH, USER_AGENT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

db = SqliteDatabase(DB_PATH)

CODE_TYPE_INTERNAL = 0  # 容器内部账号助力码
CODE_TYPE_AUTHOR = 1  # 作者助力码
CODE_TYPE_POOL = 2  # 助力池助力码

FLAG_TYPE_POST = 1  # 是否已提交助力码
FLAG_TYPE_GET = 2  # 是否已获取助力池助力码


def sign(data, api_key='4ff4d7df-e07d-31a9-b746-97328ca9241d'):
    """
    :param api_key:
    :param data:
    :return:
    """
    if "sign" in data:
        data.pop('sign')
    data_list = []
    for key in sorted(data):
        if data[key]:
            data_list.append("%s=%s" % (key, data[key]))
    data = "&".join(data_list).strip() + api_key.strip()
    md5 = hashlib.md5()
    md5.update(data.encode(encoding='UTF-8'))
    return md5.hexdigest()


class CodeFlag(Model):
    """
    助力码标志
    """
    flag_type = SmallIntegerField(verbose_name='标志类型', default=0)  # 1获取云端助力码, 2提交助力码

    code_key = CharField(verbose_name='邀请/助力码标示', max_length=30)

    done = BooleanField(verbose_name='是否完成', default=False)  # 当天是否已完成, false/true

    created_at = DateField(verbose_name='创建日期', default=datetime.now().date())

    updated_at = DateField(verbose_name='更新日期', default=datetime.now().date())

    class Meta:
        database = db
        table_name = 'code_flag'

    @classmethod
    def is_post_codes(cls, code_key=''):
        """
        是否已提交助力码
        """
        try:
            res = cls.get(cls.code_key == code_key, cls.flag_type == FLAG_TYPE_POST, cls.created_at == datetime.now().date())
            if res and res.done:
                return True
            else:
                return False
        except Exception as e:
            return False

    @classmethod
    def is_pull_codes(cls, code_key=''):
        """
        是否已拉取助力码
        """
        try:
            res = cls.get(cls.code_key == code_key, cls.flag_type == FLAG_TYPE_GET, cls.created_at ==
                          datetime.now().date())
            if res and res.done:
                return True
            else:
                return False
        except Exception as e:
            return False

    @classmethod
    def del_pull_codes(cls, code_key):
        """
        删除拉取助力码的标志位
        """
        try:
            return cls.delete().where(cls.code_key == code_key)
        except Exception as e:
            return False

    @classmethod
    def set_post_codes(cls, code_key=''):
        """
        标记为已提交助力码
        """
        cls.insert(code_key=code_key, flag_type=FLAG_TYPE_POST, done=True,
                   created_at=datetime.now().date()).execute()

    @classmethod
    def set_pull_codes(cls, code_key=''):
        """
        标记为已拉取助力码
        """
        cls.insert(code_key=code_key, flag_type=FLAG_TYPE_GET, done=True,
                   created_at=datetime.now().date()).execute()


class Code(Model):
    """
    邀请/助力码
    """
    account = CharField(verbose_name='京东账号', max_length=255)

    code_type = SmallIntegerField(verbose_name='邀请/助力码标示', default=0)  # 0 容器内部账号, 1作者, 2助力池

    code_key = CharField(verbose_name='邀请/助力码标示', max_length=30)

    code_val = CharField(verbose_name='邀请/助力码内容', max_length=255)

    sort = SmallIntegerField(verbose_name='排序字段', default=1)

    created_at = DateField(verbose_name='创建日期', default=datetime.now().date())

    updated_at = DateField(verbose_name='更新日期', default=datetime.now().date())

    class Meta:
        database = db
        table_name = 'code'

    @classmethod
    def insert_code(cls, code_key=None, account='', code_val='', code_type=CODE_TYPE_INTERNAL, sort=1):
        """
        插入一条助力码
        :param sort:
        :param code_val:
        :param account:
        :param code_key:
        :param code_type: 0 容器内部账号, 1作者, 2助力池
        :return:
        """
        exists = cls.select().where(cls.code_key == code_key, cls.code_val == code_val,
                                    cls.sort == sort, cls.code_type == code_type,
                                    cls.created_at == datetime.now().date()).exists()
        if not exists:
            rowid = (cls.insert(code_key=code_key, account=account,
                                code_val=code_val, code_type=code_type, sort=sort,
                                created_at=datetime.now().date()).execute())
            return rowid

        cls.update({cls.code_val: code_val, cls.sort: sort}).where(cls.account == account,
                                                                   cls.code_key == code_key,
                                                                   cls.created_at == datetime.now().date(),
                                                                   ).execute()

    @classmethod
    def pull_code_list(cls, code_key='', limit=200):
        """
        拉取助力码
        """
        # 今日已拉取助力码, 跳过!
        if CodeFlag.is_pull_codes(code_key):
            return []

        try:
            url = 'https://cqpy5frn58.execute-api.ap-east-1.amazonaws.com/production'
            headers = {
                'user-agent': USER_AGENT,
                'content-type': 'application/json'
            }
            params = {
                'count': limit,
                'code_key': code_key
            }
            params['sign'] = sign(params)
            response = requests.get(url=url, params=params, timeout=20, verify=False, headers=headers)
            if response.json()['code'] == 0:
                CodeFlag.set_pull_codes(code_key)
            items = response.json()['data']
            ins_data = []

            for item in items:
                ins_data.append({
                    'account': item['account'],
                    'code_val': item['code'],
                    'code_key': code_key,
                    'code_type': CODE_TYPE_POOL,
                })
            cls.insert_many(ins_data).execute()
            return items
        except Exception as e:
            print('获取随机助力列表失败, {}'.format(e.args))
            return []

    @classmethod
    def get_code_list(cls, code_key=''):
        """
        获取助力码列表
        :param code_key: 助力码类型
        :return:
        """
        result = []

        # 容器内部助力码
        internal_code_list = cls.select().where(cls.code_key == code_key,
                                                cls.created_at == datetime.now().date(),
                                                cls.code_type == CODE_TYPE_INTERNAL).order_by(
            cls.sort).execute()

        for code in internal_code_list:
            if not code.code_val:
                continue
            result.append({
                'account': code.account,
                'code': code.code_val,
            })

        try:
            author = cls.get(cls.code_key == code_key,
                             cls.created_at == datetime.now().date(),
                             cls.code_type == CODE_TYPE_AUTHOR)

            if author and author.code_val:
                result.append({
                    'account': author.account,
                    'code': author.code_val,
                })
        except Exception as e:
            pass

        # 随机取助力池20个助力码
        pool_code_list = cls.select().where(cls.code_type == CODE_TYPE_POOL,
                                            cls.code_key == code_key).order_by(fn.Random()).limit(20)
        temp = []
        for code in pool_code_list:
            if not code or not code.code_val:
                continue
            temp.append({
                'account': code.account,
                'code': code.code_val,
            })
        random.shuffle(temp)
        result.extend(temp)
        return reduce(lambda x, y: x if y in x else x + [y], [[], ] + result)

    @classmethod
    def post_code_list(cls, code_key):
        """
        提交助力码
        :return:
        """
        # 今日已提交助力码
        if CodeFlag.is_post_codes(code_key):
            print('今日已提交过该类型助力码!')
            return False

        timeout = random.random() * 10
        print('正在提交助力码, 随机等待:{}秒...'.format(timeout))
        time.sleep(timeout)

        code_list = []
        # 获取容器内部账号助力码
        item_list = cls.select().where(cls.code_key == code_key, cls.created_at == datetime.now().date(),
                                       cls.code_type == CODE_TYPE_INTERNAL).order_by(cls.sort).execute()
        for item in item_list:
            code_list.append({
                'account': item.account,
                'code_key': item.code_key,
                'code_val': item.code_val,
            })

        if len(code_list) < 1:
            return

        url = 'https://cqpy5frn58.execute-api.ap-east-1.amazonaws.com/production'
        params = {
            'items': code_list,
            'os': os.getenv('HOSTNAME', '')
        }
        params['sign'] = sign(params)

        try:
            headers = {
                'user-agent': USER_AGENT,
                'Content-Type': 'application/json'
            }
            response = requests.post(url, json=params, verify=False, timeout=20, headers=headers)
            if response.json().get('code') == 0:
                CodeFlag.set_post_codes(code_key)
                print('成功提交助力码!')
            else:
                print(response.json())
                print('提交助力码失败!')
        except Exception as e:
            print('提交助力码失败, {}'.format(e.args))


db.create_tables([Code, CodeFlag])
