#!/usr/local/bin/python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/23 下午4:33
# @Project : jd_scripts
# @File    : update_readme.py
# @Cron    :
# @Desc    :
import re
import sys
import os


def get_script_list(dir_path=None):
    """
    获取脚本列表
    :return:
    """
    script_list = []
    if not dir_path:
        return script_list
    file_list = [file for file in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, file))]
    for filename in file_list:
        if not filename.endswith('.py') or filename.startswith('test') or filename.startswith('config'):
            continue
        script_list.append(filename)
    script_list.sort()
    return script_list


def generate_table(base_dir, script_list):
    """
    生成脚本表格
    :return:
    """
    table_str = "|脚本名称|脚本描述|\n|:---:|:---:|\n"
    for script in script_list:
        script_path = os.path.join(base_dir, script)
        with open(script_path, 'r', encoding='utf-8-sig') as f:
            text = f.read()
            comment = re.search(r'@Desc.*:(.*)', text)
            if comment:
                comment_text = comment.group(1)
            else:
                comment_text = ''
            table_str += '|{}|{}|\n'.format(script, comment_text)

    return table_str


def update_readme():
    """
    更新README.md
    :return:
    """
    base_dir = os.path.split(os.path.abspath(sys.argv[0]))[0].replace('tools', '')
    readme_path = os.path.join(base_dir, 'README.md')

    with open(readme_path, 'r', encoding='utf-8-sig') as f:
        text = f.read()

    split_text = '## 脚本列表'
    # 原来的内容
    content = text.split(split_text)[0]

    script_list = get_script_list(base_dir)

    table = generate_table(base_dir, script_list)

    result = content + '\n\n' + split_text + '\n\n' + '- **脚本总数: {}**'.format(len(script_list)) + '\n\n' + table

    with open(readme_path, 'w', encoding='utf-8-sig') as f:
        f.write(result)


if __name__ == '__main__':
    update_readme()
