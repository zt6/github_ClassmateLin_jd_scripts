#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/3 下午7:24
# @Project : jd_scripts
# @File    : jd_puzzle_sign.py
# @Cron    : 47 10,4 * * *
# @Desc    : 京东APP->拼图签到合集
import asyncio
from utils.console import println
from utils.jd_init import jd_init
from utils.browser import open_browser, open_page, close_browser
from config import USER_AGENT
from utils.validate import puzzle_validate_decorator
from utils.logger import logger


@jd_init
@puzzle_validate_decorator
class JdPuzzleSign:
    """
    京东拼图签到
    """
    browser_cookies = []
    user_agent = 'jdapp;' + USER_AGENT

    @logger.catch
    async def sign(self, browser, url='', name=''):

        println('{}, 正在打开{}页面...'.format(self.account, name))
        page = await open_page(browser, url, self.user_agent, self.browser_cookies)
        if not page:
            println('{}, 打开{}页面失败, 无法签到!'.format(self.account, name))
            return

        sign_button_selector = 'div.sign_btn'

        try:
            await page.waitForSelector(sign_button_selector, timeout=50000)
        except Exception as e:
            println('{}, 无法加载签到按钮, {}'.format(self.account, e.args))

        try:
            sign_button_element = await page.querySelector(sign_button_selector)
            sign_button_text = await (await sign_button_element.getProperty("textContent")).jsonValue()
        except Exception as e:
            println('{}, {}查找签到按钮失败, {}'.format(self.account, name, e))
            return
        if sign_button_text.strip() != '立即翻牌':
            println('{}, {}今日已签到!'.format(self.account, name))
            return

        println('{}, 点击立即翻牌, 进行签到！'.format(self.account))
        for i in range(10):  # 报系统频繁需要点击多次
            await sign_button_element.click()
            await asyncio.sleep(1)
        await page.evaluate(('''() => {
                                document.getElementsByClassName('man-machine-container')[0].style.cssText += 'width:400px;height:299px';
                                                }'''))
        await asyncio.sleep(2)

        validator_box_selector = 'div.man-machine-container'

        true = await self.puzzle_validate(page, validator_box_selector)
        if true:
            println('{}, {}签到成功!'.format(self.account, name))
        else:
            println('{}, {}签到失败!'.format(self.account, name))

    @logger.catch
    async def undies_sign(self, browser):
        """
        京东内衣签到
        :return:
        """
        url = 'https://pro.m.jd.com/mall/active/4PgpL1xqPSW1sVXCJ3xopDbB1f69/index.html#/'
        name = '京东内衣'
        await self.sign(browser, url, name)

    @logger.catch
    async def children_clothing_sign(self, browser):
        """
        京东童装签到
        :param browser:
        :return:
        """
        url = 'https://pro.m.jd.com/mall/active/3Af6mZNcf5m795T8dtDVfDwWVNhJ/index.html#/'
        name = '京东童装'
        await self.sign(browser, url, name)

    @logger.catch
    async def purifying_sign(self, browser):
        url = 'https://pro.m.jd.com/mall/active/2Tjm6ay1ZbZ3v7UbriTj6kHy9dn6/index.html'
        name = '清洁馆'
        await self.sign(browser, url, name)

    @logger.catch
    async def baby_sign(self, browser):
        """
        母婴馆签到
        :param browser:
        :return:
        """
        url = 'https://pro.m.jd.com/mall/active/3BbAVGQPDd6vTyHYjmAutXrKAos6/index.html?collectionId=87'
        name = '母婴馆'
        await self.sign(browser, url, name)

    @logger.catch
    async def personal_care_sign(self, browser):
        """
        个护签到
        :param browser:
        :return:
        """
        url = 'https://prodev.m.jd.com/mall/active/2tZssTgnQsiUqhmg5ooLSHY9XSeN/index.html?collectionId=294'
        name = '个护馆'
        await self.sign(browser, url, name)

    @logger.catch
    async def supermarket_sign(self, browser):
        """
        京东超市签到
        :param browser:
        :return:
        """
        url = 'https://pro.m.jd.com/mall/active/QPwDgLSops2bcsYqQ57hENGrjgj/index.html?babelChannel=ttt2&tttparams' \
              '=6Bu7w0meyJnTGF0IjoiMjMuMDE1NDExIiwiZ0xuZyI6IjExMy4zODgwOTIifQ7%3D%3D&'
        name = '京东超市'
        await self.sign(browser, url, name)

    @logger.catch
    async def digital_3C(self, browser):
        """
        数码3C签到
        :param browser:
        :return:
        """
        url = 'https://prodev.m.jd.com/mall/active/4SWjnZSCTHPYjE5T7j35rxxuMTb6/index.html?babelChannel=ttt5' \
              '&collectionId=450&tttparams=u4jfb2vfeyJnTGF0IjoiMjMuMDE1NDExIiwiZ0xuZyI6IjExMy4zODgwOTIifQ8%3D%3D'
        name = '数码3C'
        await self.sign(browser, url, name)

    @logger.catch
    async def electrical_appliance(self, browser):
        """
        京东电器签到
        :param browser:
        :return:
        """
        url = 'https://prodev.m.jd.com/mall/active/4SWjnZSCTHPYjE5T7j35rxxuMTb6/index.html'
        name = '京东电器'
        await self.sign(browser, url, name)

    async def plus(self, browser):
        """
        plus会员店
        :param browser:
        :return:
        """
        url = 'https://prodev.m.jd.com/mall/active/3bhgbFe5HZcFCjEZf2jzp3umx4ZR/index.html'
        name = 'plus天天领京豆'
        await self.sign(browser, url, name)

    @logger.catch
    async def run(self):
        """
        签到入口
        :return:
        """
        self.browser_cookies = [
            {
                'domain': '.jd.com',
                'name': 'pt_pin',
                'value': self.cookies.get('pt_pin'),
            },
            {
                'domain': '.jd.com',
                'name': 'pt_key',
                'value': self.cookies.get('pt_key'),
            }
        ]
        println('{}, 正在打开浏览器...'.format(self.account))
        browser = await open_browser()

        await self.undies_sign(browser)  # 京东内衣
        await asyncio.sleep(1)
        await self.children_clothing_sign(browser)  # 京东童装
        await asyncio.sleep(1)
        await self.baby_sign(browser)  # 母婴馆
        await asyncio.sleep(1)
        await self.digital_3C(browser)
        await asyncio.sleep(1)
        await self.supermarket_sign(browser)  # 京东超市签到
        await asyncio.sleep(1)
        await self.electrical_appliance(browser)  # 京东电器签到
        await asyncio.sleep(1)
        await self.personal_care_sign(browser)  # 个护馆签到
        await asyncio.sleep(1)
        await self.purifying_sign(browser)  # 清洁馆
        await asyncio.sleep(1)
        await self.plus(browser)  # plus会员
        await asyncio.sleep(1)

        await close_browser(browser)


if __name__ == '__main__':
    from config import JD_PUZZLE_PROCESS_NUM
    from utils.process import process_start
    process_start(JdPuzzleSign, '京东拼图签到', process_num=JD_PUZZLE_PROCESS_NUM)

