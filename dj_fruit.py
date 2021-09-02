#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/27 2:00 下午
# @File    : dj_fruit.py
# @Project : jd_scripts
# @Cron    : 10 7,11,18 * * *
# @Desc    : 京东APP->京东到家->免费水果
import aiohttp
import json
import asyncio
from utils.console import println
from utils.logger import logger
from utils.dj_init import dj_init
from config import DJ_FRUIT_KEEP_WATER
from db.model import Code

#  到家果园助力
CODE_DJ_FRUIT = 'dj_fruit'


@dj_init
class DjFruit:
    """
    京东到家领水果
    """

    @logger.catch
    async def daily_water_award(self, session, task):
        """
        每日水滴奖励
        :param task:
        :param session:
        :return:
        """
        body = {
            "modelId": task['modelId'],
            "taskId": task['taskId'],
            "taskType": task['taskType'],
            "plateCode": 3,
            "subNode": ''
        }
        await self.finish_task(session, task['taskName'], body)

    @logger.catch
    async def daily_sign(self, session, task):
        """
        每日签到
        :param session:
        :param task:
        :return:
        """

        if task['todayFinishNum'] > 0:
            println('{}, 今日已签到!'.format(self.account))
            return

        sub_node = 'null'

        for item in task['subList']:
            if item['sendStatus'] == 0:
                sub_node = item['node']
                break

        body = {
            "modelId": task['modelId'],
            "taskId": task['taskId'],
            "taskType": task['taskType'],
            "plateCode": 3,
            "subNode": sub_node
        }
        await self.finish_task(session, task['taskName'], body)

    @logger.catch
    async def watering(self, session, times=None, batch=True, keep_water=10):
        """
        浇水
        :param times: 浇水次数
        :param session:
        :param batch: 是否批量浇水
        :param keep_water: 保留水滴
        :return:
        """
        water_info = await self.get_water_info(session)
        if not water_info:
            println('{}, 无法获取用户水滴信息!'.format(self.account))
            return

        water_balance = water_info['userWaterBalance']
        if not times:
            times = int((water_balance - keep_water) / 10)

        if water_balance - times * 10 < keep_water:
            println('{}, 执行完浇水, 剩余水滴将小于保留水滴:{}g, 故不浇水!'.format(self.account, keep_water))
            return

        if water_balance < times * 10:
            println('{}, 当前水滴:{}, 不够浇{}次水, 不浇水...'.format(self.account, water_balance, times))
            return

        if times < 1:
            println('{}, 当前不需要浇水!'.format(self.account))
            return

        println('{}, 当前水滴:{}, 需要浇水:{}次!'.format(self.account, water_balance, times))

        if batch:
            res = await self.post(session, 'fruit/watering', {"waterTime": times})
            if res['code'] != '0':
                println('{}, {}次浇水失败!'.format(self.account, times))
            else:
                println('{}, 成功浇水{}次!'.format(self.account, times))
            return

        for i in range(1, times + 1):
            res = await self.post(session, 'fruit/watering', {"waterTime": 1})
            if res['code'] != '0':
                println('{}, 第{}次浇水失败, 不再浇水!'.format(self.account, i))
                break
            else:
                println('{}, 第{}次浇水成功!'.format(self.account, i))

    @logger.catch
    async def receive_water_red_packet(self, session):
        """
        领取浇水红包
        :param session:
        :return:
        """
        res = await self.get(session, 'fruit/getWaterRedPackInfo')
        if res['code'] != '0' or 'result' not in res:
            println('{}, 查询浇水红包信息失败!'.format(self.account))
            return
        rest_progress = float(res.get('result', dict()).get('restProgress', '10'))
        if rest_progress > 0.0:
            println('{}, 浇水红包差{}可以打开!'.format(self.account, rest_progress))
            return

        res = await self.get(session, 'fruit/receiveWaterRedPack')
        if res['code'] != '0':
            println('{}, 打开浇水红包失败!'.format(self.account))
        else:
            println('{}, 成功打开浇水红包!'.format(self.account))

    @logger.catch
    async def receive_water_bottle(self, session):
        """
        领取水瓶
        :param session:
        :return:
        """
        res = await self.get(session, 'fruit/receiveWaterBottle')
        if res['code'] != '0':
            println('{}, 领取水瓶水滴失败, {}!'.format(self.account, res.get('msg')))
        else:
            println('{}, 成功领水瓶水滴!'.format(self.account))

    @logger.catch
    async def do_task(self, session):
        """
        做任务
        :param session:
        :return:
        """
        res = await self.get(session, 'task/list', {"modelId": "M10007", "plateCode": 3})

        if res['code'] != '0':
            println('{}, 获取任务列表失败!'.format(self.account))
            return

        data = res['result']
        task_list = data['taskInfoList']

        for i in range(len(task_list)):
            task = task_list[i]
            task_name = task['taskName']
            task_type = task['taskType']

            if task_type in [506, 513]:  # 下单奖励, 超级多单任务
                println('{}, 任务:《{}》无法完成, 请手动执行!'.format(self.account, task_name))
                continue

            if task['status'] == 3:  # 任务完成并且领取了水滴
                println('{}, 任务:《{}》今日已完成!'.format(self.account, task_name))
                continue

            if task['status'] == 2:  # 任务完成，但未领水滴
                await self.get_task_award(session, task)
                continue

            if task_type == 1101:  # 签到任务
                await self.daily_sign(session, task)
            elif task_type == 1102:  # 定时领水滴
                await self.finish_task(session, task_name, {"modelId": task['modelId'], "taskId": task['taskId'],
                                                            "taskType": task['taskType'], "plateCode": 3})
            elif task_type == 1103:  # 每日领水滴
                await self.daily_water_award(session, task)
            elif task_type in [307, 310, 901, 502]:  # 浏览类型任务
                await self.browse_task(session, task)
                await self.get_task_award(session, task)
            elif task_type == 1104:  # 邀请好友领水果
                pass
            elif task_type == 1201:  # 鲜豆签到, 好友助力任务
                await self.receive_task(session, task)
                await self.get_share_code(task)
            elif task_type == 0:  # 浇水任务
                if 'todayFinishNum' in task:
                    times = 15 - task['todayFinishNum']
                else:
                    times = task['totalNum'] - task['finishNum']
                await self.watering(session, times=times, batch=False)  # 浇水10次
                await self.get_task_award(session, task)
            else:
                println(task)
                println('{}, 任务:《{}》暂未实现!'.format(self.account, task_name))

    @logger.catch
    async def get_water_info(self, session):
        """
        获取水滴信息
        :param session:
        :return:
        """
        res = await self.get(session, 'fruit/getWaterWheelInfo')
        if res['code'] != '0':
            return None
        return res['result']

    @logger.catch
    async def receive_water_wheel(self, session):
        """
        收取水车水滴
        :param session:
        :return:
        """
        # water_info = await self.get_water_info(session)
        # if not water_info:
        #     println('{}, 查询水滴信息失败!'.format(self.account))
        #     return
        # if water_info['waterStorage'] < water_info['capacityLimit']:
        #     println('{}, 水车水滴未满, 暂不收取!'.format(self.account))
        #     return

        res = await self.get(session, 'fruit/collectWater')
        if res['code'] != '0':
            println('{}, 收取水车水滴失败!'.format(self.account))
        else:
            println('{}, 成功收取水车水滴!'.format(self.account))

    @logger.catch
    async def get_share_code(self, task):
        """
        获取助力码
        """
        body = {
            'taskId': task['taskId'],
            'uniqueId': task['uniqueId'],
            'assistTargetPin': self.dj_pin,
        }
        code = json.dumps(body)
        Code.insert_code(code_key=CODE_DJ_FRUIT, code_val=code, account=self.account, sort=self.sort)
        println('{}, 助力码:{}'.format(self.account, code))
        return code

    @logger.catch
    async def init(self, session):
        """
        初始化
        """
        await self.request(session, 'userInfo/login')
        res = await self.post(session, 'fruit/initFruit', {
            "cityId": str(self.city_id), "longitude": self.lng, "latitude": self.lat})
        if res['code'] != '0':
            message = '未知'
            if 'msg' in res:
                message = res['msg']
            println('{}, 初始化失败, 原因:{}'.format(self.account, message))
            notify_message = '活动名称】到家果园\n【京东账号】{}\n【任务状态】执行失败\n【错误信息】{}\n'.format(self.account, message)
            self.message = notify_message
            return False
        return res['result']

    @logger.catch
    async def help_friend(self, session):
        """
        助力好友
        :return:
        """
        item_list = Code.get_code_list(CODE_DJ_FRUIT)
        for item in item_list:
            try:
                account, code = item.get('account'), item.get('code')
                if account == self.account:
                    continue
                params = json.loads(code)
            except Exception as e:
                println('{}, 助力失败, 助力码错误, {}'.format(self.account, e.args))
                continue
            if 'assistTargetPin' not in params:
                println('{}, 助力码错误, 无法助力!'.format(self.account))
                continue

            params.update({
                "plateCode": 5,
                "modelId": "M10007",
                "taskType": 1201,
            })
            user_pin = params['assistTargetPin']

            res = await self.get(session, 'task/finished', params)
            if res['code'] != '0':
                println(res)
                println('{}, 助力好友:{}失败, {}'.format(self.account, user_pin, res))
                break
            else:
                println('{}, 成功助力好友:{}!'.format(self.account, user_pin))
                await asyncio.sleep(1)

    @logger.catch
    async def set_notify_message(self, session):
        """
        设置通知消息
        :param session:
        :return:
        """
        data = await self.init(session)
        if not data:
            return
        active_info = data['activityInfoResponse']
        message = '【活动名称】到家果园\n【活动账号】{}\n'.format(self.account)
        message += '【奖品名称】{}\n'.format(active_info['fruitName'])
        message += '【{}进度】{}/{}\n'.format(
            active_info['stageName'],
            round(float(active_info['curStageTotalProcess']) - float(active_info['curStageLeftProcess']), 2),
            active_info['curStageTotalProcess'])
        if active_info['ifMaxProcess']:
            message += '【温馨提示】奖品可领取，请前往京东APP-京东到家-领免费水果领取, 并种植新一轮奖品!'

        message += '【剩余水滴】{}\n'.format(data['userResponse']['waterBalance'])

        self.message = message

    async def run(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            dj_cookies = await self.login(session)
            if not dj_cookies:
                return
            println('{}, 登录成功...'.format(self.account))

        async with aiohttp.ClientSession(cookies=dj_cookies, headers=self.headers) as session:
            result = await self.init(session)
            if not result:
                return
            await self.do_task(session)  # 做任务
            await self.receive_water_red_packet(session)  # 领取浇水红包
            await self.receive_water_bottle(session)  # 领取水瓶
            await self.receive_water_wheel(session)  # 领取水车
            await self.watering(session, batch=False, keep_water=DJ_FRUIT_KEEP_WATER)
            await self.set_notify_message(session)

    async def run_help(self):
        """
        :return:
        """
        async with aiohttp.ClientSession(cookies=self.cookies, headers=self.headers) as session:
            dj_cookies = await self.login(session)
            if not dj_cookies:
                return
            println('{}, 登录成功...'.format(self.account))

        async with aiohttp.ClientSession(cookies=dj_cookies, headers=self.headers) as session:
            await self.help_friend(session)


if __name__ == '__main__':
    # from config import JD_COOKIES
    # app = DjFruit(**JD_COOKIES[0])
    # asyncio.run(app.run())
    from utils.process import process_start
    process_start(DjFruit, '到家果园', code_key=CODE_DJ_FRUIT)
