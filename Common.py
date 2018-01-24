#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: wuzhixiang
# Email: wuzhixiang@eccom.com.cn

from __future__ import print_function
from credentials import URL, LOGIN, PASSWORD
import requests
import urllib3
import yaml
import sys, getopt, time, threading
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
    except Exception, e:
        print("\nLogin failed :")
        if ('imdata' in result.json()):
            for i in range(int(result.json()['totalCount'].encode('utf-8'))):
                print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        else:
            print(e.message)
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
    except Exception, e:
        print("\nOperation failed :")
        if ('imdata' in result.json()):
            for i in range(int(result.json()['totalCount'].encode('utf-8'))):
                print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        else:
            print(e.message)
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
            print('============================================================')
            job = j['job']
            tasklist = job['tasklist']
            # 备份
            if('tenant' in job):
                take_snapshot(job['tenant'])
            print('------------------------------------------------------------')
            print('Performing Job: %s ...' % (job['description']))
            for t in tasklist:
                task = t['task']
                print('------------------------------------------------------------')
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
                print('\r')
        print('============================================================')
        print('\nPlayBooks Performed!\n')


def take_snapshot(tenantName):
    """
    创建快照以便出错恢复

    :param tenantName: 租户名称
    """
    print('Taking snapshot for Tenant: %s' % tenantName)
    if(tenantExist(tenantName)):
        snapshot_count = query_snapshot(tenantName)['totalCount']
        snapshot_url = URL + '/api/node/mo/uni/fabric/configexp-defaultOneTime.json'
        payload = '''
        {
            "configExportP": {
                "attributes": {
                    "dn": "uni/fabric/configexp-defaultOneTime",
                    "name": "defaultOneTime",
                    "snapshot": "true",
                    "targetDn": "uni/tn-%s",
                    "adminSt": "triggered",
                    "rn": "configexp-defaultOneTime",
                    "status": "created,modified"
                },
                "children": []
            }
        }
        ''' % tenantName

        headers = {"Content-Type": "application/json"}
        result = session.post(url=snapshot_url, data=payload, headers=headers, verify=False)

        try:
            result.raise_for_status()
        except Exception, e:
            print("\nOperation failed :")
            if ('imdata' in result.json()):
                for i in range(int(result.json()['totalCount'].encode('utf-8'))):
                    print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
            else:
                print(e.message)
            sys.exit()

        print('Waiting for snapshot taking...')
        snapshot = query_snapshot(tenantName)
        while (snapshot_count == snapshot['totalCount']):
            time.sleep(1)
            snapshot = query_snapshot(tenantName)
        print('New snapshot:', snapshot['imdata'][int(snapshot['totalCount']) - 1]['configSnapshot']['attributes']['name'],
              ' created!')
    else:
        choice = raw_input('No tenant named %s . Do you want to continue?(y/n)\t' % tenantName)
        if(choice.lower() !=  'y'):
            exit(0)


def query_snapshot(tenantName):
    """
    查询快照信息

    :param tenantName: 租户名称
    :return: 租户下的所有快照
    """
    snapshot_url = URL + '/api/node/class/configSnapshot.json'
    params = {'query-target-filter': 'and(eq(configSnapshot.rootDn,"uni/tn-%s"))' % tenantName}
    headers = {"Content-Type": "application/json"}
    result = session.get(url=snapshot_url, params=params, headers=headers, verify=False)
    try:
        result.raise_for_status()
    except Exception, e:
        print("\nOperation failed :")
        if ('imdata' in result.json()):
            for i in range(int(result.json()['totalCount'].encode('utf-8'))):
                print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        else:
            print(e.message)
        sys.exit()
    return result.json()


def tenantExist(tenantName):
    """
    查询租户是否存在
    """
    tenant_url = URL + '/api/mo/uni/tn-%s.json' % tenantName
    params = {}
    headers = {"Content-Type": "application/json"}
    result = session.get(url=tenant_url, params=params, headers=headers, verify=False)
    try:
        result.raise_for_status()
    except Exception, e:
        print("\nOperation failed :")
        if ('imdata' in result.json()):
            for i in range(int(result.json()['totalCount'].encode('utf-8'))):
                print("\t", result.json()['imdata'][i]['error']['attributes']['text'])
        else:
            print(e.message)
        sys.exit()
    return True if eval(result.json()['totalCount']) else False


def refresh():
    """
    刷新Token
    """
    refresh_url = URL + '/api/aaaRefresh.json'
    headers = {"Content-Type": "application/json"}
    while (True):
        time.sleep(200)
        session.get(url=refresh_url, headers=headers, verify=False)


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
    # 刷新线程
    t = threading.Thread(target=refresh)
    t.setDaemon(True)
    t.start()
    # 获取编排信息
    playBooks = get_playbooks(playbooksFile)
    # 执行
    execute(playBooks)


if __name__ == '__main__':
    main(sys.argv[1:])
