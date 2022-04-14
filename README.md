## python3 学习资源

- [python3 cookbook](https://python3-cookbook.readthedocs.io/zh_CN/latest/preface.html)
- [awesome-python](https://github.com/jobbole/awesome-python-cn)
## 环境

- python版本:3.7.*

### 本地运行

- `pip install virtualenv`
- `git clone https://github.com/ClassmateLin/jd_scripts.git`
- `cd jd_scripts`
- `virtualenv venv && source ./venv/bin/activate`
- `pip install -r requirements.txt`
- `mkdir conf && cp .config.yaml ./conf/`
- 查看conf/config.yaml配置项, 每个脚本均可以单独运行。


### docker 运行

- 方式一:
  - `docker run -itd --name jd classmatelin/scripts:latest`
  - docker exec -it jd /bin/bash
  - vim conf/config.yaml配置。

- 方式二:
  - mkdir jd && cd jd
  - vim docker-composer.yaml

  ```
  version: "3"

  services:
    jd:
      container_name: jd
      image: classmatelin/scripts:v1
      volumes:
        - ./conf/:/scripts/conf
        - ./logs:/scripts/logs
      environment:
        REPO_URL: https://github.com/ClassmateLin/scripts.git
      dns:
        - 8.8.8.8
        - 114.114.114.114
        - 119.29.29.29
      privileged: true
      restart: always
  ```
  - docker-composer up -d
  - vim conf/config.yaml.

## 特别声明: 

* 本仓库发布的jd_scripts项目中涉及的任何解锁和解密分析脚本，仅用于测试和学习研究，禁止用于商业用途，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断.

* 本项目内所有资源文件，禁止任何公众号、自媒体进行任何形式的转载、发布。

* ClassmateLin对任何脚本问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害.

* 间接使用脚本的任何用户在某些行为违反国家/地区法律或相关法规的情况下进行传播, ClassmateLin对于由此引起的任何隐私泄漏或其他后果概不负责.

* 请勿将jd_scripts项目的任何内容用于商业或非法目的，否则后果自负.

* 如果任何单位或个人认为该项目的脚本可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，本人将在收到认证文件后删除相关脚本.

* 以任何方式查看此项目的人或直接或间接使用该jd_scripts项目的任何脚本的使用者都应仔细阅读此声明。ClassmateLin保留随时更改或补充此免责声明的权利。一旦使用并复制了任何相关脚本或jd_scripts项目的规则，则视为您已接受此免责声明.

**您必须在下载后的24小时内从计算机或手机中完全删除以上内容.**  </br>
***您使用或者复制了本仓库且本人制作的任何脚本，则视为`已接受`此声明，请仔细阅读*** 


## 其他

- ***backup 目录下的脚本为已过期脚本***

- ***conf/config.yaml 中的crontab_exclude_scripts的配置项配合config/crontab.sh可实现自定义脚本执行。***

- 如果我的项目对您有帮助:

<img src="https://classmatelin.top/upload/2022/01/571641820763_.pic-7b8e58ed85294d7caf606decfbd8bbce.jpg" width="400" height="400">


## 脚本列表

- **脚本总数: 45**

|脚本名称|脚本描述|
|:---:|:---:|
|check_cookies.py| 检查cookies是否过期, 过期则发送通知|
|clean_log.py| 清除日志, 默认保留三天, 可在配置中修改|
|dj_bean.py| 京东APP->京东到家->签到->所有任务|
|dj_bean_manor.py| 京东APP->京东到家->签到->鲜豆庄园|
|dj_bean_manor_water.py| 京东APP->京东到家->签到->鲜豆庄园, 定时领水滴/浇水|
|dj_fruit.py| 京东APP->京东到家->免费水果|
|dj_fruit_collect.py| 京东APP->京东到家->免费水果, 定时领水滴/浇水|
|dj_notification.py| 京东到家活动通知|
|jd_5g_box.py| 京东APP->营业厅->领京豆, 5G盲盒做任务抽奖|
|jd_5g_box_collect.py|  京东APP->营业厅->领京豆, 5G盲盒每3小时收取信号值|
|jd_bean_home.py| 京东APP->我的->签到领京豆->领额外奖励|
|jd_big_winner.py| 京东急速版APP->我的->发财大赢家|
|jd_car.py| 京东汽车|
|jd_car_exchange.py| 京东汽车兑换|
|jd_cash.py| 京东APP->搜索领现金进入|
|jd_collar_bean.py| 京东APP首页->领京豆->升级赚京豆|
|jd_cute_pet.py| 京东APP->我的->东东萌宠|
|jd_earn.py| 微信小程序->京东赚赚|
|jd_factory.py| 京东APP->京东电器->东东工厂|
|jd_factory_collect.py| 京东APP->京东电器->东东工厂, 定时收电量|
|jd_farm.py| 京东APP-我的->东东农场|
|jd_flash_sale_box.py| 京东APP->品牌闪购->闪购盲盒|
|jd_free_trials.py||
|jd_gold_creator.py| 京东APP->排行榜->金榜创造营|
|jd_good_morning.py| 京东APP首页->领京豆->早起福利|
|jd_health.py| 京东APP->我的->签到领豆->边玩边赚->东东健康社区|
|jd_health_collect.py| 京东APP->我的->签到领豆->边玩边赚->东东健康社区, 定时收能量|
|jd_notification.py| 京东活动通知|
|jd_planting_bean.py| 京东APP->我的->签到领豆->种豆得豆|
|jd_planting_bean_collect.py| 京东APP->我的->签到领豆->种豆得豆, 定时收取营养液|
|jd_polite.py| 小鸽有礼|
|jd_second_coin.py| 京东APP首页->京东秒杀->立即签到->赚秒秒币|
|jd_shark_bean.py| 京东APP->我的->签到领豆->摇京豆|
|jd_shop.py| 京东APP首页->领京豆->进店领豆|
|jd_sign.py| 京东签到合集|
|jd_smash_golden_egg.py| 京东APP-每日特价-疯狂砸金蛋|
|jd_speed_red_packet.py| 京东极速版红包-自动提现微信现金|
|jd_speed_sign.py| 京东极速版app 签到和金币任务|
|jd_super_brand.py| 特务Z|
|jd_unsubscribe.py| 取消商品关注和店铺关注|
|jd_wishing_pool.py| 京东APP首页->京东众筹->众筹许愿池|
|jd_wonderful_lottery.py| 京东APP->签到领豆->边玩边赚->每日抽奖|
|jx_factory.py| 京喜App->我的->京喜工厂|
|jx_factory_collect.py| 京喜App->我的->京喜工厂, 定时收电量|
|jx_sign.py| 京喜APP->首页->签到领红包|
