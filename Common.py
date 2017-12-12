#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import print_function
from credentials import URL, LOGIN, PASSWORD
import requests
import urllib3
import json
import sys
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
    print("POST  ", login_url)
    result = session.post(url=login_url, data=payload, headers=headers, verify=False)
    try:
        result.raise_for_status()
    except:
        print("\nLogin failed :")
        for i in range(int(result.json()['totalCount'].encode('utf-8'))):
            print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        sys.exit()


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
        print(u'模板读取失败：%s' % e)
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
    print("\nPOST  ", epg_url)
    result = session.post(url=epg_url, data=payload, headers=headers, verify=False)

    try:
        result.raise_for_status()
    except:
        print("Operation failed :")
        for i in range(int(result.json()['totalCount'].encode('utf-8'))):
            print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        sys.exit()

    print("result: ", result, '\n')


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
        print(u'excel表格读取失败：%s' % e)
        return None


def main():
    # 登陆apic
    login()
    # 获取模板
    baseTemplate = get_template('template.json')
    # 获取自定义配置项
    configList = Excel2List('data.xlsx')
    # 逐条推送
    for config in configList:
        do_post(config, baseTemplate)


if __name__ == '__main__':
    main()
