#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/3/29 15:06
# @Author  : CaiQinYi
# @Site    : 
# @File    : cfgyaml.py
# @Software: PyCharm

import yaml
import os
import json


# 获取当前脚本所在文件夹路径
curPath = os.path.dirname(os.path.realpath(__file__))
# 获取yaml文件路径
yamlPath = os.path.join(curPath, "cfgyaml.yaml")

# open方法打开直接读出来
f = open(yamlPath, 'r', encoding='utf-8')
cfg = f.read()
# print(type(cfg))  # 读出来是字符串
# print(cfg)

source_dict = yaml.load(cfg,Loader=yaml.FullLoader)  # 用load方法转字典

# print(json.dumps(source_dict,indent=4))
# print(source_dict['partner']['limit']['excludedProvinces'])
# print(json.dumps(d,indent=4))
# print(type(d))

# source_dict = {
#     "fadada.config": {
#         "appId": {
#             'bb':8899
#         },
#         "version": 2.5,
#         "age": 30,
#     }
# }

def operate_len1(config_dict,config_list,config_value):
    config_dict[config_list[0]] = config_value
def operate_len2(config_dict,config_list,config_value):
    config_dict[config_list[0]][config_list[1]] = config_value
def operate_len3(config_dict,config_list,config_value):
    print(type(config_value),type(config_list))
    config_dict[config_list[0]][config_list[1]][config_list[2]] = config_value
def operate_len4(config_dict,config_list,config_value):
    config_dict[config_list[0]][config_list[1]][config_list[2]][config_list[3]] = config_value
def operate_len5(config_dict,config_list,config_value):
    config_dict[config_list[0]][config_list[1]][config_list[2]][config_list[3]][config_list[4]] = config_value
def operate_len6(config_dict,config_list,config_value):
    config_dict[config_list[0]][config_list[1]][config_list[2]][config_list[3]][config_list[4]][config_list[5]] = config_value


str1 = "partner:limit:excludedProvinces = dict{'abc':1,'bac':2}"
# str1 = "fadada.config:version:age = 31 \npartner:limit:excludedProvinces = ['abc','bac']"
config_lists = str1.split('\n')
for config_list in config_lists:
    key_list = config_list.split('=')[0].replace(' ', '').split(':')
    value = config_list.split('=')[1].replace(' ','')
    value = eval(value)
    if len(key_list) == 1:
        operate_len1(source_dict,key_list,value)
        continue
    if len(key_list) == 2:
        operate_len2(source_dict,key_list,value)
        continue
    if len(key_list) == 3:
        operate_len3(source_dict,key_list,value)
        continue
    if len(key_list) == 4:
        operate_len4(source_dict,key_list,value)
        continue
    if len(key_list) == 5:
        operate_len5(source_dict,key_list,value)
        continue
    if len(key_list) == 6:
        operate_len6(source_dict,key_list,value)

# print(json.dumps(source_dict,indent=4))

# print(json.dumps(DICT2))
# # for k,v in a.items():
# #     print(k,v)
# def print_dict(input_dict):
#     if isinstance(input_dict,dict):
#         for k,v in input_dict.items():
#             return v
#
# while True:
#     print(print_dict(a))


# test = '{"fadada.config":{"appId":9085,"version":1.1}}'
# change_dict = json.loads(test)
# a['fadada.config']['appId'] = '11'
# print(json.dumps(a,indent=4))

# print(json.dumps(a,indent=4))
# dict = {'Name': 'Zara', 'Age': 7}
# dict2 = {'Age': 'female' }
# dict.update(dict2)
# print("Value : %s" %  dict)