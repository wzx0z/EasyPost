#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: wuzhixiang
# Email: wuzhixiang@eccom.com.cn

from __future__ import print_function
from credentials import URL, LOGIN, PASSWORD
import requests
import urllib3
import yaml
import sys, getopt, time
import xlrd

# 关闭urllib3的警告信息
urllib3.disable_warnings()
# 全局session
session = requests.Session()


def login():
    """
    登陆 APIC
    """
    login_url = URL + '/api/aaaLogin.json'
    payload = '{"aaaUser":{"attributes":{"name":"%s","pwd":"%s"}}}}' % (LOGIN, PASSWORD)
    headers = {"Content-Type": "application/json"}
    print("Login APIC ...")
    result = session.post(url=login_url, data=payload, headers=headers, verify=False)
    try:
        result.raise_for_status()
    except:
        print("\Login failed :")
        for i in range(int(result.json()['totalCount'].encode('utf-8'))):
            print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        sys.exit()
    print("Login success! Read playbooks ...")


def get_template(file_path):
    """
    获取模板信息

    :param file_path: template.json路径
    :return: 模板信息
    """
    try:
        data = open(file_path).read()
        return data
    except Exception as e:
        print(u'模板读取失败：%s\n' % e)
        sys.exit(2)
        return None


def do_post(data, PAYLOAD_TEMPLATE):
    """
    向apic推送配置

    :param data: 用于模板的数据字典
    :param PAYLOAD_TEMPLATE: 用于推送的模板
    """
    if 'api_url' in data and data['api_url'] != '':
        epg_url = URL + data['api_url']
    else:
        epg_url = URL + '/api/mo/uni.json'

    payload = PAYLOAD_TEMPLATE % data

    headers = {"Content-Type": "application/json"}
    # print("\nPOST  ", epg_url)
    result = session.post(url=epg_url, data=payload, headers=headers, verify=False)

    try:
        result.raise_for_status()
    except:
        print("\nOperation failed :")
        for i in range(int(result.json()['totalCount'].encode('utf-8'))):
            print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        sys.exit()


def Excel2List(file_path):
    """
    将Excel中的信息转换为List对象

    :param file_path: data.xlsx路径
    :return: N条自定义数据项组成List对象
    """
    if get_data(file_path) is not None:
        book = get_data(file_path)
        sheet = book.sheet_by_index(0)
        row_0 = sheet.row(0)
        nrows = sheet.nrows
        ncols = sheet.ncols

        configList = []

        for i in range(nrows):
            if i == 0:
                continue
            config = {}
            for j in range(ncols):
                config[str(row_0[j]).split("'")[1]] = str(sheet.row_values(i)[j])
            configList.append(config)
    return configList


def get_data(file_path):
    """
    获取模板信息

    :param file_path: data.xlsx路径
    :return: excel表格信息
    """
    try:
        data = xlrd.open_workbook(file_path)
        return data
    except Exception as e:
        print(u'excel表格读取失败：%s\n' % e)
        sys.exit(2)
        return None

def get_playbooks(file_path):
    """
    获取编排信息

    :param file_path: playbooks.yaml路径
    :return: 编排信息
    """
    try:
        data = open(file_path).read()
        playbooks = yaml.load(data)
        return playbooks
    except Exception as e:
        print(u'编排信息读取失败：%s\n' % e)
        sys.exit(2)
        return None

def execute(playbooks):
    """
    执行编排

    :param playbooks: playbooks
    """
    if playbooks is not None:
        for j in playbooks:
            job = j['job']
            tasklist = job['tasklist']
            print('\nPerforming Job:%s ...'%(job['description']))
            for t in tasklist:
                task = t['task']
                print("Task:", task['description'])
                # 获取模板
                baseTemplate = get_template(task['template'])
                # 获取自定义配置项
                configList = Excel2List(task['sourcedata'])
                # 逐条推送
                index = 1
                for config in configList:
                    sys.stdout.write('Processing task %d/%d\r' % (index, len(configList)))
                    sys.stdout.flush()
                    do_post(config, baseTemplate)
                    index = index + 1
                    time.sleep(0.5)
                print('\nTasks Done!')
        print('\nPlayBooks Performed!\n')


def main(argv):
    if len(argv) == 0:
        print('Usage: Common.py -p <playbooks>')
        sys.exit(2)
    try:
        opts, args = getopt.getopt(argv, "hp:", ["playbooks="])
    except getopt.GetoptError:
        print('Usage: Common.py -p <playbooks>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('Usage: Common.py -p <playbooks>')
            sys.exit()
        elif opt in ("-p", "--playbooks"):
            playbooksFile = arg
    # 登陆apic
    login()
    # 获取编排信息
    playBooks = get_playbooks(playbooksFile)
    execute(playBooks)


if __name__ == '__main__':
    main(sys.argv[1:])
