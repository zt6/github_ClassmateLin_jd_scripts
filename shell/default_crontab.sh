# 默认定时任务

SHELL=/bin/sh

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# 定时更新脚本
40 4,23 * * * /bin/docker-entrypoint >> /dev/null  2>&1

#  检查cookies是否过期, 过期则发送通知
0 */2 * * * /scripts/check_cookies.py >> /scripts/logs/check_cookies_`date "+\%Y-\%m-\%d"`.log 2>&1

#  清除日志, 默认保留三天, 可在配置中修改
30 23 * * * /scripts/clean_log.py >> /scripts/logs/clean_log_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东到家->签到->所有任务
45 7,12,19 * * * /scripts/dj_bean.py >> /scripts/logs/dj_bean_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东到家->签到->鲜豆庄园
30 6,21 * * * /scripts/dj_bean_manor.py >> /scripts/logs/dj_bean_manor_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东到家->签到->鲜豆庄园, 定时领水滴/浇水
*/40 * * * * /scripts/dj_bean_manor_water.py >> /scripts/logs/dj_bean_manor_water_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东到家->免费水果
10 7,11,18 * * * /scripts/dj_fruit.py >> /scripts/logs/dj_fruit_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东到家->免费水果, 定时领水滴/浇水
42 */1 * * * /scripts/dj_fruit_collect.py >> /scripts/logs/dj_fruit_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->营业厅->领京豆, 5G盲盒做任务抽奖
8 0 * * * /scripts/jd_5g_box.py >> /scripts/logs/jd_5g_box_`date "+\%Y-\%m-\%d"`.log 2>&1

#   京东APP->营业厅->领京豆, 5G盲盒每3小时收取信号值
27 */3 * * * /scripts/jd_5g_box_collect.py >> /scripts/logs/jd_5g_box_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->签到领豆->边玩边赚->京小鸽游乐寄
45 8,15 * * * /scripts/jd_amusement_post.py >> /scripts/logs/jd_amusement_post_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京豆红包变动通知
15 */8 * * * /scripts/jd_bean_change.py >> /scripts/logs/jd_bean_change_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领京豆->领额外奖励
45 0 * * * /scripts/jd_bean_home.py >> /scripts/logs/jd_bean_home_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东急速版APP->我的->发财大赢家
3 */1 * * * /scripts/jd_big_winner.py >> /scripts/logs/jd_big_winner_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->搜索领现金进入
46 */12 * * * /scripts/jd_cash.py >> /scripts/logs/jd_cash_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP首页->领京豆->升级赚京豆
6 1 * * * /scripts/jd_collar_bean.py >> /scripts/logs/jd_collar_bean_`date "+\%Y-\%m-\%d"`.log 2>&1

#  清凉一夏
8 8 * * * /scripts/jd_cool_summer.py >> /scripts/logs/jd_cool_summer_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->东东萌宠
35 6-18/6 * * * /scripts/jd_cute_pet.py >> /scripts/logs/jd_cute_pet_`date "+\%Y-\%m-\%d"`.log 2>&1

#  微信小程序->京东赚赚
10 10 * * * /scripts/jd_earn.py >> /scripts/logs/jd_earn_`date "+\%Y-\%m-\%d"`.log 2>&1

#  赚京豆(微信小程序)-赚京豆-签到领京豆
45 5,22 * * * /scripts/jd_earn_bean.py >> /scripts/logs/jd_earn_bean_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东电器->东东工厂
30 6-18/6 * * * /scripts/jd_factory.py >> /scripts/logs/jd_factory_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->京东电器->东东工厂, 定时收电量
10 */1 * * * /scripts/jd_factory_collect.py >> /scripts/logs/jd_factory_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP-我的->东东农场
15 6-18/6 * * * /scripts/jd_farm.py >> /scripts/logs/jd_farm_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->品牌闪购->闪购盲盒
15 5,23 * * * /scripts/jd_flash_sale_box.py >> /scripts/logs/jd_flash_sale_box_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->排行榜->金榜创造营
30 7,19 * * * /scripts/jd_gold_creator.py >> /scripts/logs/jd_gold_creator_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP首页->领京豆->早起福利
30 6 * * * /scripts/jd_good_morning.py >> /scripts/logs/jd_good_morning_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领豆->边玩边赚->东东健康社区
35 6,16 * * * /scripts/jd_health.py >> /scripts/logs/jd_health_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领豆->边玩边赚->东东健康社区, 定时收能量
0 */30 * * * /scripts/jd_health_collect.py >> /scripts/logs/jd_health_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->宠汪汪
45 8,12,17 * * * /scripts/jd_joy.py >> /scripts/logs/jd_joy_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->宠汪汪, 兑换京豆, 优先兑换500, 兑换失败则兑换20.
56 7,15,23 * * * /scripts/jd_joy_exchange.py >> /scripts/logs/jd_joy_exchange_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->宠汪汪, 定时喂狗
10 */3 * * * /scripts/jd_joy_feed.py >> /scripts/logs/jd_joy_feed_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP-签到领豆-边玩边赚-玩锦鲤红包
40 0,22 * * * /scripts/jd_koi_red_packet.py >> /scripts/logs/jd_koi_red_packet_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->签到领京豆->抽京豆
6 0 * * * /scripts/jd_lottery_bean.py >> /scripts/logs/jd_lottery_bean_`date "+\%Y-\%m-\%d"`.log 2>&1

#  幸运大转盘, 入口忘了在哪
10 10,23 * * * /scripts/jd_lucky_turntable.py >> /scripts/logs/jd_lucky_turntable_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领豆->种豆得豆
10 3,15 * * * /scripts/jd_planting_bean.py >> /scripts/logs/jd_planting_bean_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领豆->种豆得豆, 定时收取营养液
40 */2 * * * /scripts/jd_planting_bean_collect.py >> /scripts/logs/jd_planting_bean_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  小鸽有礼
9 16 * * * /scripts/jd_polite.py >> /scripts/logs/jd_polite_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->拼图签到合集
47 10,4 * * * /scripts/jd_puzzle_sign.py >> /scripts/logs/jd_puzzle_sign_`date "+\%Y-\%m-\%d"`.log 2>&1

#  今日王牌, 入口忘了在哪。
21 9 * * * /scripts/jd_ranking_list.py >> /scripts/logs/jd_ranking_list_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领豆->边玩边赚->开学充电站
1 3 * * * /scripts/jd_school_charging.py >> /scripts/logs/jd_school_charging_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP首页->京东秒杀->立即签到->赚秒秒币
12 11 * * * /scripts/jd_second_coin.py >> /scripts/logs/jd_second_coin_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->签到领豆->摇京豆
6 0,18,23 * * * /scripts/jd_shark_bean.py >> /scripts/logs/jd_shark_bean_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP首页->领京豆->进店领豆
1 0 * * * /scripts/jd_shop.py >> /scripts/logs/jd_shop_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东签到合集
0 3,19 * * * /scripts/jd_sign.py >> /scripts/logs/jd_sign_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP-每日特价-疯狂砸金蛋
21 5,17 * * * /scripts/jd_smash_golden_egg.py >> /scripts/logs/jd_smash_golden_egg_`date "+\%Y-\%m-\%d"`.log 2>&1

#  特务Z
30 10,22 * * * /scripts/jd_super_brand.py >> /scripts/logs/jd_super_brand_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP首页->京东超市->游戏
7 7,20 * * * /scripts/jd_supermarket.py >> /scripts/logs/jd_supermarket_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->更多工具->新品试用
25 12 * * * /scripts/jd_try.py >> /scripts/logs/jd_try_`date "+\%Y-\%m-\%d"`.log 2>&1

#  取消商品关注和店铺关注
50 23 * * * /scripts/jd_unsubscribe.py >> /scripts/logs/jd_unsubscribe_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP首页->京东众筹->众筹许愿池
45 */12 * * * /scripts/jd_wishing_pool.py >> /scripts/logs/jd_wishing_pool_`date "+\%Y-\%m-\%d"`.log 2>&1

#  女装盲盒
5 1 * * * /scripts/jd_women_box.py >> /scripts/logs/jd_women_box_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->签到领豆->边玩边赚->每日抽奖
44 4,5 * * * /scripts/jd_wonderful_lottery.py >> /scripts/logs/jd_wonderful_lottery_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东金融APP->天天提鹅
35 9,22 * * * /scripts/jr_daily_take_goose.py >> /scripts/logs/jr_daily_take_goose_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东金融APP->天天提鹅， 定时收鹅蛋
17 */1 * * * /scripts/jr_daily_take_goose_collect.py >> /scripts/logs/jr_daily_take_goose_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->摇钱树
5 10,21 * * * /scripts/jr_money_tree.py >> /scripts/logs/jr_money_tree_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东APP->我的->摇钱树, 定时收金果
35  */1 * * * /scripts/jr_money_tree_collect.py >> /scripts/logs/jr_money_tree_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京东金融APP->我的->养猪猪
23 0-23/8 * * * /scripts/jr_pet_pig.py >> /scripts/logs/jr_pet_pig_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京喜App->我的->京喜工厂
38 7,12,18 * * * /scripts/jx_factory.py >> /scripts/logs/jx_factory_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京喜App->我的->京喜工厂, 定时收电量
45 */1 * * * /scripts/jx_factory_collect.py >> /scripts/logs/jx_factory_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京喜APP->京喜牧场->日常任务
35 6,16 * * * /scripts/jx_pasture.py >> /scripts/logs/jx_pasture_`date "+\%Y-\%m-\%d"`.log 2>&1

#  京喜APP->京喜牧场->定时收金币/割草/投喂小鸡
40 */1 * * * /scripts/jx_pasture_collect.py >> /scripts/logs/jx_pasture_collect_`date "+\%Y-\%m-\%d"`.log 2>&1

