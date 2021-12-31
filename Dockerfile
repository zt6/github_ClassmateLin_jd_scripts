FROM python:3.7.11-slim-buster

ENV CODE_DIR=/scripts

COPY ./requirements.txt ./shell/docker-entrypoint.sh /root/

RUN apt update -y \
    && apt install -y bash vim cron git gconf-service gcc build-essential libxext6 libxfixes3 procps libxi6 \
    libxrandr2 libxrender1 libcairo2 libcups2 libdbus-1-3 \
    libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 \
    libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 \
    libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxss1 libxtst6 libappindicator1 libnss3 libasound2 \
    libatk1.0-0 libc6 ca-certificates fonts-liberation lsb-release xdg-utils \
    && chsh -s /bin/bash \
    && echo Asia/Shanghai > /etc/timezone && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && export LC_ALL="C.UTF-8" \
    && mkdir -p /root/.ssh /root/.pip \
    && ssh-keyscan github.com > /root/.ssh/known_hosts \
    && bash -c "echo -e '[global]\nindex-url = https://pypi.mirrors.ustc.edu.cn/simple/\n' > /root/.pip/pip.conf" \
    && pip install -U pip --no-cache-dir && pip install -r /root/requirements.txt --no-cache-dir \
    && chmod a+x /root/docker-entrypoint.sh && mv /root/docker-entrypoint.sh /bin/docker-entrypoint \
    && apt clean && rm -rf /root/.cache/pip && rm -rf /root/requirements.txt

ENTRYPOINT ["/bin/docker-entrypoint"]

CMD ["/bin/bash"]

WORKDIR $CODE_DIR