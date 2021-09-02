#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/6/25 1:25 下午
# @File    : jx_factory.py
# @Project : jd_scripts
# @Cron    : 38 7,12,18 * * *
# @Desc    : 京喜App->我的->京喜工厂
import moment
import time
import re
import json
import aiohttp
import asyncio
from furl import furl
from datetime import datetime
from urllib.parse import urlencode
from utils.jx_init import jx_init
from utils.console import println
from utils.process import get_code_list
from utils.logger import logger
from db.model import Code


# 京喜工厂开团
CODE_JX_FACTORY_TUAN = 'jx_factory_tuan'

# 惊喜工厂招工
CODE_JX_FACTORY_WORK = 'jx_factory_work'


@jx_init
class JxFactory:
    """
    京喜工厂
    """
    headers = {
        'referer': 'https://st.jingxi.com/',
        'user-agent': 'jdpingou;android;4.11.0;11;a27b83d3d1dba1cc;network/wifi;model/RMX2121;appBuild/17304;partner'
                      '/oppo01;;session/136;aid/a27b83d3d1dba1cc;oaid/;pap/JA2019_3111789;brand/realme;eu'
                      '/1623732683334633;fv/4613462616133636;Mozilla/5.0 (Linux; Android 11; RMX2121 '
                      'Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                      'Chrome/91.0.4472.120 Mobile Safari/537.36'
    }

    host = 'https://m.jingxi.com/'
    factory_id = None  # 工厂ID
    factory_name = ''  # 工厂名称
    nickname = None  # 用户昵称
    encrypt_pin = None
    inserted_electric = 0  # 已投入电量
    need_electric = 0  # 总共需要的电量
    production_id = 0  # 商品ID
    production_stage_progress = ''  # 生产进度
    phone_id = ''  # 设备ID
    random = None  #
    can_help = True  # 是否能帮好友打工
    active_id = ''
    commodity_dim_id = None
    production_name = None

    @logger.catch
    async def request(self, session, path, params, method='GET'):
        """
        """
        try:
            time_ = datetime.now()
            default_params = {
                '_time': int(time_.timestamp() * 1000),
                'g_ty': 'ls',
                'callback': '',
                'sceneval': '2',
                'g_login_type': '1',
                '_': int(time_.timestamp() * 1000) + 2,
                '_ste': '1',
                'timeStamp': int(time.time() * 1000),
            }
            params.update(default_params)
            url = self.host + path + '?' + urlencode(params)
            h5st = await self.encrypt(time_, url)
            params['h5st'] = h5st
            url = self.host + path + '?' + urlencode(params)
            if method == 'GET':
                response = await session.get(url=url)
            else:
                response = await session.post(url=url)
            text = await response.text()
            data = json.loads(text)
            if data['ret'] != 0:
                return data
            else:
                result = data['data']
                result['ret'] = 0
                return result
        except Exception as e:
            println('{}, 请求服务器数据失败:{}'.format(self.account, e.args))
            return {
                'ret': 50000,
                'msg': '请求服务器失败'
            }

    @logger.catch
    async def get_user_info_by_pin(self, session, pin):
        """
        根据pin获取用户信息
        :param session:
        :param pin:
        :return:
        """
        path = 'dreamfactory/userinfo/GetUserInfoByPin'
        params = {
            'zone': 'dream_factory',
            'pin': pin,
            'sharePin': '',
            'shareType': '',
            'materialTuanPin': '',
            'materialTuanId': '',
            'source': '',
            '_stk': '_time,materialTuanId,materialTuanPin,pin,sharePin,shareType,source,zone',
        }
        data = await self.request(session, path, params)
        if not data or data['ret'] != 0:
            return None
        return data

    @logger.catch
    async def get_user_info(self, session):
        """
        获取用户信息
        """
        path = 'dreamfactory/userinfo/GetUserInfo'
        params = {
            'pin': '',
            'sharePin': '',
            'shareType': '',
            'materialTuanPin': '',
            'materialTuanId': '',
            'source': '',
            'zone': 'dream_factory'
        }
        data = await self.request(session, path, params)
        if data['ret'] != 0:
            println('{}, 获取用户数据失败, {}!'.format(self.account, data['msg']))
            return None
        return data

    @logger.catch
    async def query_friend_list(self, session):
        """
        查询好友列表
        :param session:
        :return:
        """
        println('{}, 正在获取好友信息列表...'.format(self.account))
        res = []
        path = 'dreamfactory/friend/QueryFactoryManagerList'
        params = {
            'sort': 0,
            '_stk': '_time,sort,zone',
            'zone': 'dream_factory',
        }
        data = await self.request(session, path, params)
        if not data or data['ret'] != 0:
            println('{}, 获取好友列表失败!'.format(self.account))
            return []

        friend_list = data['list']

        for friend in friend_list:
            if 'encryptPin' not in friend:
                continue
            res.append(friend['encryptPin'])
        println('{}, 成功获取{}个好友信息!'.format(self.account, len(res)))
        return res

    @logger.catch
    async def help_friend(self, session):
        """
        帮好友打工
        :param session:
        :return:
        """
        path = 'dreamfactory/friend/AssistFriend'
        body = {
            'zone': 'dream_factory',
            'sharepin': '',
            '_stk': '_time,sharepin,zone'
        }
        item_list = Code.get_code_list(CODE_JX_FACTORY_WORK)
        item_list.extend(get_code_list(CODE_JX_FACTORY_WORK))
        for item in item_list:
            account, code = item.get('account'), item.get('code')
            if account == self.account:
                continue
            body['sharepin'] = code
            res = await self.request(session, path, body)
            if res.get('ret', -1) != 0:
                println('{}, 无法助力好友:{}, {}'.format(self.account, account, res.get('msg', '原因未知')))
                if res.get('ret', -1) in [11009, 11005]:
                    break
            else:
                println('{}, 成功助力好友:{}!'.format(self.account, account))
            await asyncio.sleep(1)

    @logger.catch
    async def collect_friend_electricity(self, session):
        """
        收取好友电量
        :param session:
        :return:
        """
        friend_pin_list = await self.query_friend_list(session)

        for friend_pin in friend_pin_list:
            friend_info = await self.get_user_info_by_pin(session, friend_pin)
            await asyncio.sleep(0.2)
            if not friend_info:
                continue
            if friend_info['ret'] != 0:
                continue
            if 'factoryList' not in friend_info or not friend_info['factoryList']:
                continue

            if 'user' not in friend_info or not friend_info['user']:
                continue

            factory_id = friend_info['factoryList'][0]['factoryId']
            pin = friend_info['user']['pin']
            nickname = friend_info['user']['nickname']
            status = await self.query_user_electricity(session, factory_id=factory_id, pin=pin, nickname=nickname)
            if status == -1:  # 今日收取好友电量达到上限
                return
            await asyncio.sleep(1)

    @logger.catch
    async def collect_user_electricity(self, session, phone_id=None, factory_id=None,
                                       nickname=None, pin=None, double_flag=1):
        """
        收取发电机电量, 默认收取自己的
        :param pin:
        :param nickname:
        :param double_flag: 是否翻倍
        :param factory_id: 工厂ID
        :param phone_id: 手机设备ID
        :param session:
        :return:
        """
        path = 'dreamfactory/generator/CollectCurrentElectricity'

        if not phone_id:
            phone_id = self.phone_id
        if not factory_id:
            factory_id = self.factory_id
        if not nickname:
            nickname = self.nickname
        params = {
            'pgtimestamp': str(int(time.time() * 1000)),
            'apptoken': '',
            'phoneID': phone_id,
            'factoryid': factory_id,
            'doubleflag': double_flag,
            'timeStamp': 'undefined',
            '_stk': '_time,apptoken,doubleflag,factoryid,pgtimestamp,phoneID,zone',
            'zone': 'dream_factory',
        }
        if pin:
            params['master'] = pin
            params['_stk'] = '_time,apptoken,doubleflag,factoryid,master,pgtimestamp,phoneID,zone'
        data = await self.request(session, path, params, 'GET')
        if not data or data['ret'] != 0:
            println('{}, 收取用户:{}的电量失败, {}'.format(self.account, nickname, data))
            if data['ret'] == 11010:
                return -1
        else:
            println('{}, 成功收取用户:{}的电量:{}!'.format(self.account, nickname, data['CollectElectricity']))

    @logger.catch
    async def query_user_electricity(self, session, factory_id=None, phone_id=None, nickname=None, pin=None):
        """
        查询当前用户发电机电量, 如果满了就收取电量
        """
        if not factory_id:
            factory_id = self.factory_id
        if not phone_id:
            phone_id = self.phone_id
        if not nickname:
            nickname = self.nickname

        path = 'dreamfactory/generator/QueryCurrentElectricityQuantity'
        body = {
            'factoryid': factory_id,
            '_stk': '_time,factoryid,zone',
            'zone': 'dream_factory'
        }
        if pin:
            body['master'] = pin
            body['_stk'] = '_time,factoryid,master,zone'
        data = await self.request(session, path, body)
        if data['ret'] != 0:
            println('{}, 查询电量失败！'.format(self.account))
            return

        if int(data['currentElectricityQuantity']) >= data['maxElectricityQuantity']:
            return await self.collect_user_electricity(session, phone_id, factory_id, nickname, pin)
        else:
            println('{}, 用户:{}, 当前电量:{}/{}, 不收取!'.format(self.account,
                                                         nickname, int(data['currentElectricityQuantity']),
                                                         data['maxElectricityQuantity']))

    @logger.catch
    async def get_active_id(self, session):
        """
        获取每期拼团的活动ID
        :param session:
        :return:
        """
        try:
            println('{}, 正在获取拼团活动ID...'.format(self.account))
            url = 'https://wqsd.jd.com/pingou/dream_factory/index.html'
            response = await session.get(url)
            text = await response.text()
            res = re.search(r'window\._CONFIG = (.*) ;var __getImgUrl', text).group(1)
            data = json.loads(res)
            for item in data:
                if 'skinConfig' not in item:
                    continue
                conf_list = item['skinConfig']
                for conf in conf_list:
                    if 'adConfig' not in conf:
                        continue
                    ad_list = conf['adConfig']
                    for ad in ad_list:
                        if not ad['start'] or not ad['end']:
                            continue
                        start_date = moment.date(ad['start'])
                        end_date = moment.date(ad['end'])
                        now = moment.now()
                        if start_date < now < end_date:
                            url = furl(ad['link'].split(',')[0])
                            active_id = url.args.get('activeId', '')
                            println('{}, 拼团活动ID为:{}'.format(self.account, active_id))
                            return active_id
        except Exception as e:
            println('{}, 获取拼团活动ID失败, {}!'.format(self.account, e.args))
            return ''

    @logger.catch
    async def query_production_name(self, session):
        """
        查询商品名称
        :param session:
        :return:
        """
        path = 'dreamfactory/diminfo/GetCommodityDetails'
        body = {
            'zone': 'dream_factory',
            'commodityId': self.commodity_dim_id
        }
        res = await self.request(session, path, body)
        if not res.get('commodityList', None):
            self.production_name = '获取失败'
        else:
            self.production_name = res['commodityList'][0]['name']

    @logger.catch
    async def init(self, session):
        """
        初始化
        """
        user_info = await self.get_user_info(session)
        if not user_info:
            return False
        if 'factoryList' not in user_info or not user_info['factoryList']:
            self.message = '\n【活动名称】京喜工厂\n【京东账号】{}\n【活动未开启】请前往京喜APP-我的-京喜工厂开启活动并选择商品!'.format(self.account)
            return False

        self.factory_id = user_info['factoryList'][0]['factoryId']
        if 'productionList' not in user_info or not user_info['productionList']:
            println('{}, 未选择商品!'.format(self.account))
        else:
            self.inserted_electric = user_info['productionList'][0]['investedElectric']
            self.need_electric = user_info['productionList'][0]['needElectric']
            self.production_id = user_info['productionList'][0]['productionId']
            self.commodity_dim_id = user_info['productionList'][0]['commodityDimId']
            self.production_stage_progress = round((self.inserted_electric / self.need_electric) * 100, 2)
        if 'user' not in user_info:
            println('{}, 没有找到用户信息!'.format(self.account))
            return False
        await asyncio.sleep(0.5)
        await self.query_production_name(session)

        self.pin = user_info['user']['pin']
        self.phone_id = user_info['user']['deviceId']
        self.encrypt_pin = user_info['user']['encryptPin']
        self.nickname = user_info['user']['nickname']

        println('{}, 助力码:{}'.format(self.account, self.encrypt_pin))

        Code.insert_code(code_key=CODE_JX_FACTORY_WORK, code_val=self.encrypt_pin, sort=self.sort, account=self.account)

        self.active_id = await self.get_active_id(session)

        return True

    @logger.catch
    async def query_work_info(self, session):
        """
        查询招工/打工情况
        :param session:
        :return:
        """
        path = 'dreamfactory/friend/QueryFriendList'
        params = {
            'body': '',
            '_stk': '_time,zone',
            'zone': 'dream_factory',
        }
        data = await self.request(session, path, params)
        if not data:
            return
        println('{}, 今日帮好友打工:{}/{}次!'.format(self.account, len(data['assistListToday']), data['assistNumMax']))

        # 打工次数满了，无法打工
        if len(data['assistListToday']) >= data['assistNumMax']:
            self.can_help = False

        println('{}, 今日招工:{}/{}次!'.format(self.account, len(data['hireListToday']), data['hireNumMax']))

    @logger.catch
    async def get_task_award(self, session, task):
        """
        领取任务奖励
        :param task:
        :param session:
        :return:
        """
        path = 'newtasksys/newtasksys_front/Award'
        params = {
            'bizCode': 'dream_factory',
            'source': 'dream_factory',
            'taskId': task['taskId'],
            '_stk': '_time,bizCode,source,taskId'
        }
        data = await self.request(session, path, params)

        if not data or data['ret'] != 0:
            println('{}, 领取任务:《{}》奖励失败, {}'.format(self.account, task['taskName'], data['msg']))
            return
        num = data['prizeInfo'].replace('\n', '')
        println('{}, 领取任务:《{}》奖励成功, 获得电力:{}!'.format(self.account, task['taskName'], num))

    @logger.catch
    async def do_task_list(self, session):
        """
        获取任务列表
        :param session:
        :return:
        """
        path = 'newtasksys/newtasksys_front/GetUserTaskStatusList'
        params = {
            'bizCode': 'dream_factory',
            'source': 'dream_factory',
            '_stk': '_time,bizCode,source'
        }
        data = await self.request(session, path, params)
        if not data or data['ret'] != 0:
            println('{}, 获取任务列表失败!'.format(self.account))
            return
        task_list = data['userTaskStatusList']

        for task in task_list:
            # 任务完成并且没有领取过奖励去领取奖励
            if task['completedTimes'] >= task['targetTimes'] and task['awardStatus'] != 1:
                await self.get_task_award(session, task)
                await asyncio.sleep(1)
                continue

            if task['taskType'] in [2, 9]:
                await self.do_task(session, task)
                await asyncio.sleep(1)

    @logger.catch
    async def do_task(self, session, task):
        """
        做任务
        :param task:
        :param session:
        :return:
        """
        if task['completedTimes'] >= task['targetTimes']:
            println('{}, 任务《{}》今日已完成!'.format(self.account, task['taskName']))
            return

        path = 'newtasksys/newtasksys_front/DoTask'
        params = {
            'source': 'dreamfactory',
            'bizCode': 'dream_factory',
            '_stk': '_time,bizCode,configExtra,source,taskId',
            'taskId': task['taskId'],
            'configExtra': ''
        }
        for i in range(task['completedTimes'], task['targetTimes']):
            data = await self.request(session, path, params)
            if not data or data['ret'] != 0:
                break
            await asyncio.sleep(1)
            await self.get_task_award(session, task)

    @logger.catch
    async def query_tuan_info(self, session, active_id=None):
        """
        查询开团信息
        :return:
        """
        if not active_id:
            active_id = self.active_id
        path = 'dreamfactory/tuan/QueryActiveConfig'
        params = {
            'activeId': active_id,
            'tuanId': '',
            '_stk': '_time,activeId,tuanId',
        }
        data = await self.request(session, path, params)
        if not data or data['ret'] != 0:
            println('{}, 获取团ID失败!'.format(self.account))
            return []
        return data['userTuanInfo']

    @logger.catch
    async def create_tuan(self, session):
        """
        :return:
        """
        tuan_info = await self.query_tuan_info(session)
        if tuan_info['isOpenTuan'] != 2:
            path = 'dreamfactory/tuan/CreateTuan'
            params = {
                'activeId': self.active_id,
                'isOpenApp': 1,
                '_stk': '_time,activeId,isOpenApp'
            }
            data = await self.request(session, path, params)
            if not data or data['ret'] != 0:
                println('{}, 开团失败!'.format(self.account))
                return ''
            println('{}, 开团成功, 团ID：{}!'.format(self.account, data['tuanId']))
            tuan_id = data['tuanId']

        else:
            tuan_id = tuan_info['tuanId']
            
        println('{}, 团ID:{}'.format(self.account, tuan_id))
        
        Code.insert_code(code_key=CODE_JX_FACTORY_TUAN, code_val=tuan_id, sort=self.sort, account=self.account)

        return tuan_id

    @logger.catch
    async def join_tuan(self, session):
        """
        参团
        :param session:
        :return:
        """
        item_list = Code.get_code_list(CODE_JX_FACTORY_TUAN)
        item_list.extend(CODE_JX_FACTORY_TUAN)
        path = 'dreamfactory/tuan/JoinTuan'
        for item in item_list:
            if type(item) != dict:
                continue
            account, code = item.get('account', None), item.get('code', None)

            if account == self.account or not account or not code:
                continue

            params = {
                'activeId': self.active_id,
                'tuanId': code,
                '_stk': '_time,activeId,tuanId'
            }
            data = await self.request(session, path, params)

            if not data:
                println('{}, 无法参与好友:{}的团!'.format(self.account, account))
                return

            if data['ret'] in [10208, 0]:
                println('{}, 已成功参与好友:{}的团!'.format(self.account, account))
            else:
                println('{}, 无法参与好友:{}的团, {}'.format(self.account, account, data['msg']))
                if data['ret'] in [10206, 10003, 10005]:
                    break

            await asyncio.sleep(1)

    @logger.catch
    async def hire_award(self, session):
        """
        收取招工电量
        :param session:
        :return:
        """
        query_path = 'dreamfactory/friend/QueryHireReward'
        query_body = {
            'zone': 'dream_factory',
            '_stk': '_time,zone'
        }
        res = await self.request(session, query_path, query_body)

        item_list = res.get('hireReward', [])

        for item in item_list:
            path = 'dreamfactory/friend/HireAward'
            body = {
                'zone': 'dream_factory',
                'date': item['date'],
                'type': item['type'],
                '_stk': '_time,date,type,zone'
            }
            res = await self.request(session, path, body)

            if res.get('ret', -1) == 0:
                println('{}, 成功收取招工电量!'.format(self.account))
            else:
                println('{}, 收取招工电量失败, {}!'.format(self.account, res.get('msg', '原因未知')))

            await asyncio.sleep(1)

    @logger.catch
    async def invest_electric(self, session):
        """
        投入电量
        :param session:
        :return:
        """
        path = 'dreamfactory/userinfo/InvestElectric'
        body = {
            'productionId': self.production_id,
            'zone': 'dream_factory',
            '_stk': '_time,productionId,zone'
        }
        res = await self.request(session, path, body)

        if res.get('ret', -1) == 0:
            println('{}, 投入电量成功!'.format(self.account))
        else:
            println('{}, 投入电量失败!'.format(self.account))

    @logger.catch
    async def run_help(self):
        """
        :return:
        """
        await self.get_encrypt()
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            success = await self.init(session)
            if not success:
                println('{}, 初始化失败!'.format(self.account))
                return
            await self.join_tuan(session)
            await self.help_friend(session)

    @logger.catch
    async def open_box(self, session):
        """
        开盒子
        :param session:
        :return:
        """
        path = 'dreamfactory/usermaterial/GetSuggestContent'
        body = {
            'zone': 'dream_factory',
            'type': 2,
            '_stk': '_time,type,zone'
        }
        res = await self.request(session, path, body)
        println('{}, 开盒子结果:{}'.format(self.account, res.get('msg')))

    @logger.catch
    async def set_notify_msg(self, session):
        """
        :return:
        """
        await self.init(session)
        self.message = '\n【活动名称】京喜工厂\n【京东账号】{}\n【活动昵称】{}\n'.format(self.account, self.nickname)
        if not self.production_id:
            self.message += '【商品名称】当前未选择商品, 请前往京喜APP-我的-京喜工厂选择商品!\n'
        else:
            self.message += '【商品名称】{}\n【所需电量】{}\n【投入电量】{}\n'.format(self.production_name,
                                                                    self.need_electric, self.inserted_electric)
            self.message += '【生成进度】{}%\n'.format(self.production_stage_progress)

        self.message += '【活动入口】京喜APP-我的-京喜工厂'

    @logger.catch
    async def run(self):
        """
        程序入口
        """
        await self.get_encrypt()
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies) as session:
            success = await self.init(session)
            if not success:
                println('{}, 初始化失败!'.format(self.account))
                return

            await self.create_tuan(session)
            await self.query_work_info(session)
            await self.do_task_list(session)
            await self.hire_award(session)
            await self.query_user_electricity(session)
            await self.collect_friend_electricity(session)
            await self.open_box(session)
            await self.invest_electric(session)
            await self.set_notify_msg(session)


if __name__ == '__main__':
    from utils.process import process_start
    process_start(JxFactory, '京喜工厂', code_key=[CODE_JX_FACTORY_WORK, CODE_JX_FACTORY_TUAN])
