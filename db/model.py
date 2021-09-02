#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/29 1:19 下午
# @File    : model.py
# @Project : jd_scripts
# @Desc    : model定义
from datetime import datetime
from peewee import *
from config import DB_PATH

db = SqliteDatabase(DB_PATH)


class Code(Model):
    """
    邀请/助力码
    """
    account = CharField(verbose_name='京东账号', max_length=255)

    # 邀请/助力码类型L: 1容器内部账号助力码, 2云端助力码, 3,容器配置填写助力码
    code_type = SmallIntegerField(verbose_name='邀请/助力码标示', default=0)

    code_key = CharField(verbose_name='邀请/助力码标示', max_length=30)

    code_val = CharField(verbose_name='邀请/助力码内容', max_length=255)

    sort = SmallIntegerField(verbose_name='排序字段', default=1)

    created_at = DateField(verbose_name='创建日期', default=datetime.now().date())

    updated_at = DateField(verbose_name='更新日期', default=datetime.now().date())

    class Meta:
        database = db
        table_name = 'code'

    @classmethod
    def insert_code(cls, code_key=None, account='', code_val='', code_type=1, sort=1):
        """
        插入一条助力码
        :param sort:
        :param code_val:
        :param account:
        :param code_key:
        :param code_type:
        :return:
        """
        exists = cls.select().where(cls.code_key == code_key, cls.account == account, cls.code_val == code_val,
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
    def get_code_list(cls, code_key=''):
        """
        获取助力码列表
        :param code_key: 助力码类型
        :return:
        """
        result = []

        code_list = cls.select().where(cls.code_key == code_key, cls.created_at == datetime.now().date()).order_by(
            cls.sort).execute()
        if not code_list:
            return result

        for code in code_list:
            result.append({
                'account': code.account,
                'code': code.code_val,
            })

        return result

    @classmethod
    def get_codes(cls, code_key=''):
        """
        :param code_key:
        :return:
        """
        code_list = cls.select().where(cls.code_key == code_key, cls.created_at == datetime.now().date()).order_by(
            cls.sort).execute()
        return code_list


db.create_tables([Code])

