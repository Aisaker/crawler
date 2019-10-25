#autor:dyb
#time:2019/10/14
import json
import re
import numpy as np
import pandas as pd
import pymongo
import time
import requests
from requests.cookies import RequestsCookieJar
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
import urllib.parse
import datetime

#############config###############(百度全指数采集）######################
TIMEOUT = 5
guanjianci = ['CS75', '长安CS75', 'CS75PLUS', '长安CS75PLUS', 'CS55', '长安CS55', '哈弗H6','哈弗H6coupe','哈弗H6 coupe',
              '长城哈弗H6','吉利博越','博越','广汽传祺GS4','传祺GS4']
seriesjuhe_list = ['CS75聚合', 'CS55聚合', '哈弗H6聚合', '博越聚合', '传祺GS4聚合']#不能重名
# 所有的聚合车系
search_date=['2010-12-27','2019-10-14']
zixun_date=['2017-07-03','2019-10-14']
meiti_date=['2010-12-27','2019-10-14']
########################################################################


def get_cookie():#获取登陆cookies并存储
    chrome_driver = "C:\Program Files (x86)\Google\Chrome\Application\chromedriver"
    driver = webdriver.Chrome(executable_path=chrome_driver)
    wait = WebDriverWait(driver, TIMEOUT)
    url = "https://www.baidu.com/"
    driver.get(url=url)
    driver.delete_all_cookies()
    button = wait.until(EC.element_to_be_clickable((By.XPATH, ("//div[@id='u1']/a[@name='tj_login']"))))
    #//*[@id="u1"]/a[7]
    #// *[ @ id = "u1"] / a[7]
    button.click()
    sao = input("--请扫码--: ")
    cookie_list = driver.get_cookies()
    with open("cookie.txt", "w") as f:
        json.dump(cookie_list, f)
    driver.quit()

def login():#用cookies登陆
    """
    :return: 带有登陆信息的会话
    """
    with open("cookie.txt", "r") as f:
        cookie_list = json.load(f)

    s = requests.session()
    s.verify = False
    s.headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Host": "index.baidu.com",
        "Referer": "https://index.baidu.com/v2/main/index.html",
        "User-Agent": UserAgent().random
    }

    # 添加cookie
    jar = RequestsCookieJar()
    for cookie in cookie_list:
        jar.set(cookie["name"], cookie["value"])
    s.cookies = jar
    return s


def crawl_search(s, word):#百度指数获取
    """
    获取指数的数据
    :param s: 带有登陆信息的会话
    :return:
    """
    print("search")
    word = word.replace("（", "").replace("）", "").strip()
    # 请求搜索指数所有数据接口
    search_all_base_url = "https://index.baidu.com/api/SearchApi/index?"
    search_all_params = {
        "area": 0,
        "word": word
    }
    search_all_url = search_all_base_url + urllib.parse.urlencode(search_all_params)
    search_all_response = s.get(url=search_all_url)
    search_all_data_dict = json.loads(search_all_response.text,strict=False)
    if not search_all_data_dict.get("data"):
        return None
    ptbk_base_url = "https://index.baidu.com/Interface/ptbk?uniqid={}"
    uniqid = search_all_data_dict.get("data").get("uniqid")
    ptbk_url = ptbk_base_url.format(uniqid)
    ptbk_response = s.get(ptbk_url)
    time.sleep(3)
    # 映射表的原始数据
    map_list = json.loads(ptbk_response.text).get("data")

    # 获取搜索指数所有数据
    search_all_all = search_all_data_dict.get("data").get("userIndexes")[0].get("all").get("data")
    search_all_all_data = decrypt(map_list, search_all_all)
    search_all_all_start_date = search_all_data_dict.get("data").get("userIndexes")[0].get("all").get("startDate")
    search_all_all_end_date = search_all_data_dict.get("data").get("userIndexes")[0].get("all").get("endDate")
    index_type = "search"
    data_type = "week"

    item = {
        "word": word,
        "index_type": index_type,
        "data": search_all_all_data,
        "start_date": search_all_all_start_date,
        "end_date": search_all_all_end_date,
        "data_type": data_type
    }
    print(item)
    return item

def crawl_zixun(s, word):#资讯指数获取
    """
    获取指数的数据
    :param s: 带有登陆信息的会话
    :return:
    """
    print("zixun")
    word = word.replace("（", "").replace("）", "").strip()
    # 请求指数所有数据接口
    search_all_base_url = "https://index.baidu.com/api/FeedSearchApi/getFeedIndex?"
    search_all_params = {
        "area": 0,
        "word": word
    }
    search_all_url = search_all_base_url + urllib.parse.urlencode(search_all_params)
    search_all_response = s.get(url=search_all_url)
    search_all_data_dict = json.loads(search_all_response.text,strict=False)
    if not search_all_data_dict.get("data"):
        return None
    ptbk_base_url = "https://index.baidu.com/Interface/ptbk?uniqid={}"
    uniqid = search_all_data_dict.get("data").get("uniqid")
    ptbk_url = ptbk_base_url.format(uniqid)
    ptbk_response = s.get(ptbk_url)
    time.sleep(3)
    # 映射表的原始数据
    map_list = json.loads(ptbk_response.text).get("data")

    # 获取搜索指数所有数据
    search_all_all = search_all_data_dict.get("data").get("index")[0].get("data")
    search_all_all_data = decrypt(map_list, search_all_all)
    search_all_all_start_date = search_all_data_dict.get("data").get("index")[0].get("startDate")
    search_all_all_end_date = search_all_data_dict.get("data").get("index")[0].get("endDate")
    index_type = "zixun"
    data_type = "week"

    item = {
        "word": word,
        "index_type": index_type,
        "data": search_all_all_data,
        "start_date": search_all_all_start_date,
        "end_date": search_all_all_end_date,
        "data_type": data_type
    }
    print(item)
    return item

def crawl_meiti(s, word):#媒体指数获取
    """
    获取指数的数据
    :param s: 带有登陆信息的会话
    :return:
    """
    print("meiti")
    word = word.replace("（", "").replace("）", "").strip()
    # 请求指数所有数据接口
    search_all_base_url = "https://index.baidu.com/api/NewsApi/getNewsIndex?"
    search_all_params = {
        "area": 0,
        "word": word
    }
    search_all_url = search_all_base_url + urllib.parse.urlencode(search_all_params)
    search_all_response = s.get(url=search_all_url)
    search_all_data_dict = json.loads(search_all_response.text,strict=False)
    if not search_all_data_dict.get("data"):
        return None
    ptbk_base_url = "https://index.baidu.com/Interface/ptbk?uniqid={}"
    uniqid = search_all_data_dict.get("data").get("uniqid")
    ptbk_url = ptbk_base_url.format(uniqid)
    ptbk_response = s.get(ptbk_url)
    time.sleep(3)
    # 映射表的原始数据
    map_list = json.loads(ptbk_response.text).get("data")

    # 获取搜索指数所有数据
    search_all_all = search_all_data_dict.get("data").get("index")[0].get("data")
    search_all_all_data = decrypt(map_list, search_all_all)
    search_all_all_start_date = search_all_data_dict.get("data").get("index")[0].get("startDate")
    search_all_all_end_date = search_all_data_dict.get("data").get("index")[0].get("endDate")
    index_type = "meiti"
    data_type = "week"

    item = {
        "word": word,
        "index_type": index_type,
        "data": search_all_all_data,
        "start_date": search_all_all_start_date,
        "end_date": search_all_all_end_date,
        "data_type": data_type
    }
    print(item)
    return item


def decrypt(keys, encrypt_data):
    """百度指数返回结果解密"""
    w_data = {}
    for index in range(len(keys)//2):
        w_data[keys[index]] = keys[len(keys)//2 + index]

    decrypt_data = ''
    for i in range(len(encrypt_data)):
        decrypt_data += w_data[encrypt_data[i]]
    return decrypt_data


def riqiliebiao(start, end):  # 输出日期列表(按自然周）
    datestart = datetime.datetime.strptime(start, "%Y-%m-%d") + datetime.timedelta(days=-7)
    dateend = datetime.datetime.strptime(end, '%Y-%m-%d')
    aaa = []
    while datestart < dateend:
        datestart += datetime.timedelta(days=7)
        aaa.append(datestart.strftime('%Y-%m-%d'))
    return aaa

def item(guanjianci,date,searchtype):# 输出关键词dataframe结果
    guanjianci2 = guanjianci.copy()
    search_item=[]
    for i in range(len(guanjianci)):
        search_item.append(searchtype(s, guanjianci[i])['data'].split(','))
    baiduzhishubiao = pd.DataFrame(columns=guanjianci2.insert(0, 'date'))
    xinriqi = riqiliebiao(date[0], date[1])
    # CS75 =list(eval(search_item['data']))
    for i in range(len(xinriqi)):
        new = pd.DataFrame({'date': xinriqi[i]},
                           index=[1])

        baiduzhishubiao = baiduzhishubiao.append(new, ignore_index=True)
    for i in range(len(guanjianci)):
        baiduzhishubiao[guanjianci[i]] = search_item[i].copy()
        baiduzhishubiao[guanjianci[i]].replace(to_replace=r'^\s*$', value='0', regex=True, inplace=True)
        baiduzhishubiao[guanjianci[i]] = baiduzhishubiao[guanjianci[i]].astype("int")
    return baiduzhishubiao

def zhoushuju(zixun2):#根据需求修改
    zixun=zixun2.copy()
    #zixun['date']=zixun['date'].apply(lambda x: x[0:7]).copy()
    # seriesjuhe_list = ['CS75', 'CS55', '哈弗H6', '博越', '传祺GS4']
    # 所有的聚合车系
    zixun[seriesjuhe_list[0]] = zixun.apply(lambda x: x['CS75'] + x['长安CS75']+x['长安CS75PLUS']+x['CS75PLUS'], axis=1)
    zixun[seriesjuhe_list[1]] =zixun.apply(lambda x: x['CS55'] + x['长安CS55'], axis=1)
    zixun[seriesjuhe_list[2]] =zixun.apply(lambda x: x['哈弗H6'] + x['哈弗H6 coupe']+x['哈弗H6coupe']+x['长城哈弗H6'], axis=1)
    zixun[seriesjuhe_list[3]] =zixun.apply(lambda x: x['博越'] + x['吉利博越'], axis=1)
    zixun[seriesjuhe_list[4]] =zixun.apply(lambda x: x['广汽传祺GS4'] + x['传祺GS4'], axis=1)
    copy=zixun.drop(guanjianci, axis=1)
    zixun2=copy.groupby(['date'], as_index=False).mean()
    #zixun.drop(guanjianci, axis=1,inplace=True)
    return zixun2

def yuefenshuju(zixun2):#根据需求修改
    zixun=zixun2.copy()
    zixun['date']=zixun['date'].apply(lambda x: x[0:7]).copy()
    # seriesjuhe_list = ['CS75', 'CS55', '哈弗H6', '博越', '传祺GS4']
    # 所有的聚合车系
    zixun[seriesjuhe_list[0]] = zixun.apply(lambda x: x['CS75'] + x['长安CS75']+x['长安CS75PLUS']+x['CS75PLUS'], axis=1)
    zixun[seriesjuhe_list[1]] =zixun.apply(lambda x: x['CS55'] + x['长安CS55'], axis=1)
    zixun[seriesjuhe_list[2]] =zixun.apply(lambda x: x['哈弗H6'] + x['哈弗H6 coupe']+x['哈弗H6coupe']+x['长城哈弗H6'], axis=1)
    zixun[seriesjuhe_list[3]] =zixun.apply(lambda x: x['博越'] + x['吉利博越'], axis=1)
    zixun[seriesjuhe_list[4]] =zixun.apply(lambda x: x['广汽传祺GS4'] + x['传祺GS4'], axis=1)
    copy=zixun.drop(guanjianci, axis=1)
    zixun2=copy.groupby(['date'], as_index=False).mean()
    #zixun.drop(guanjianci, axis=1,inplace=True)
    return zixun2

if __name__ == '__main__':
    s = login()
   # get_cookie()########原始表#########################
    sousuo=item(guanjianci,search_date,crawl_search)###
    meiti=item(guanjianci,meiti_date,crawl_meiti)######
    zixun=item(guanjianci,zixun_date,crawl_zixun)######
#######################################################

    sousuo2=yuefenshuju(sousuo)
    meiti2=yuefenshuju(meiti)
    zixun2=yuefenshuju(zixun)

    sousuo3 = zhoushuju(sousuo)
    meiti3 = zhoushuju(meiti)
    zixun3 = zhoushuju(zixun)
########################################################
    #数据传出excel
    writer = pd.ExcelWriter('D:/pachong.xlsx')

    sousuo2.to_excel(excel_writer=writer, sheet_name='百度指数-月份',encoding='gbk',index=False)
    zixun2.to_excel(excel_writer=writer, sheet_name='资讯指数-月份', encoding='gbk', index=False)
    meiti2.to_excel(excel_writer=writer, sheet_name='媒体指数-月份', encoding='gbk', index=False)


    sousuo3.to_excel(excel_writer=writer, sheet_name='百度指数-自然周',encoding='gbk',index=False)
    zixun3.to_excel(excel_writer=writer, sheet_name='资讯指数-自然周', encoding='gbk', index=False)
    meiti3.to_excel(excel_writer=writer, sheet_name='媒体指数-自然周', encoding='gbk', index=False)

    writer.save()
    writer.close()
