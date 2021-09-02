#!/bin/bash
echo "######开始执行更新脚本######"

if [ -z $CODE_DIR ]; then
  CODE_DIR=/scripts
fi

if [ -z $REPO_URL ]; then
  REPO_URL=https://github.com/ClassmateLin/scripts.git
fi



if [ ! -f "/root/.ssh/id_rsa" ]; then
  echo -e "-----BEGIN OPENSSH PRIVATE KEY-----\n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\n-----END OPENSSH PRIVATE KEY-----" >> /root/.ssh/id_rsa;
  chmod 600 /root/.ssh/id_rsa;
  ssh-keyscan gitee.com > /root/.ssh/known_hosts;
fi

if [ ! -d $CODE_DIR/.git ]; then
  echo "代码目录为空, 开始clone代码...";
  cd $CODE_DIR;
  git init;
  git branch -M master;
  git remote add origin $REPO_URL;
  git pull origin master;
  git branch --set-upstream-to=origin/master master;
fi

if ! type ps >/dev/null 2>&1; then
  echo "正在安装procps..."
  apt -y install procps
  apt clean;
else
    echo "procps 已安装";
fi

if ! type node >/dev/null 2>&1; then
  echo "正在安装nodejs...";
  apt -y install nodejs;
  apt clean;
else
    echo "nodejs 已安装";
fi

if ! type npm >/dev/null 2>&1; then
  echo "正在安装npm...";
  apt -y install npm;
  npm install typescript -g;
  apt clean;
else
    echo "npm 已安装";
fi

if ! type chromium >/dev/null 2>&1; then
    echo "开始安装chromium...";
    apt -y install chromium;
    apt clean;
    rm -f /root/.local/share/pyppeteer;
else
    echo 'chromium 已安装';
fi

if [ ! -d $CODE_DIR/conf ]; then
  echo "配置文件目录不存在, 创建目录...";
  mkdir -p $CODE_DIR/conf;
fi

if [ ! -d $CODE_DIR/logs ]; then
  echo "日志目录不存在, 创建目录...";
  mkdir -p $CODE_DIR/logs;
fi

if [ ! -f "$CODE_DIR/conf/config.yaml" ]; then
  echo "脚本配置文件不存在, 复制配置文件...";
  cp $CODE_DIR/.config.yaml $CODE_DIR/conf/config.yaml;
fi



if [ ! -f "$CODE_DIR/conf/crontab.sh" ]; then
  echo "自定义cron配置文件不存在, 复制配置文件..."
  cp $CODE_DIR/.crontab.sh $CODE_DIR/conf/crontab.sh;
fi


echo "git pull拉取最新代码...";
cd $CODE_DIR && git reset --hard && git pull;
echo "pip install 安装最新依赖...";
pip install -r $CODE_DIR/requirements.txt;
echo "更新docker-entrypoint...";
cp $CODE_DIR/shell/docker-entrypoint.sh /bin/docker-entrypoint;
chmod a+x /bin/docker-entrypoint;
chmod a+x /scripts/*.py;

echo "更新cron任务..."
crontab -r;
python $CODE_DIR/tools/update_config.py;
python $CODE_DIR/tools/update_default_crontab.py;

# 更新js库
python $CODE_DIR/update_nodejs.py;

cat $CODE_DIR/shell/default_crontab.sh > /tmp/crontab;
echo -e "\n" >> /tmp/crontab;

cat $CODE_DIR/conf/crontab.sh >> /tmp/crontab;

if [ ! -f "/scripts/logs/pyjs.lock" ]; then
  echo "export PATH='/scripts:$PATH'" >> /etc/profile;
  source /etc/profile;
  echo "export PATH='/scripts:$PATH'" >> ~/.bashrc;
  echo "lock" > /scripts/logs/pyjs.lock;
fi

crontab /tmp/crontab;

rm /tmp/crontab;

echo "重启cron进程...";

/etc/init.d/cron restart;

echo "######更新脚本执行完毕######";


# 保证容器不退出
tail -f /dev/null;
