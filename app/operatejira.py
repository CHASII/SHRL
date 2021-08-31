#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/15 14:16
# @Author  : CaiQinYi
# @Site    : 
# @File    : operatejira.py
# @Software: PyCharm

import time
from jira import JIRA

# Import Custom Model
from conf import settings as sets


class Jira(object):
	def __init__(self):
		self.jira = JIRA(sets.Jira['jira_host'], basic_auth=(sets.Jira['jira_user, sets.jira_pass']))

	def Create(self):
		pass

	def Update(self):
		pass

	# 删除
	def Delte(self,id):
		issue = self.jira.issue(id)
		issue.delete()
		pass

	def Info(self):
		# 匿名权限下获取所有能看到的项目
		projects = self.jira.projects()
		# for i in projects:
		# 	print(i.name)#项目名
		pass

	def Other(self):
		search_sql2 = 'project = SHRL AND fixVersion = 归档-2019.1.24 ORDER BY created ASC'
		# search_sql2 = 'project = SHRL AND issuetype = 上线发布 AND status = "已完成(待归档)"  ORDER BY created ASC'
		# print(jira.issue('SHRL-62').fields.customfield_12455.value)
		jira = JIRA(sets.jira_host, basic_auth=(sets.jira_user, sets.jira_pass))
		lists = jira.search_issues(search_sql2, maxResults=False)
		for list in lists:
			# print(list)
			# JIRA自助发布创建者
			jira_creator = jira.issue(list).fields.creator.displayName
			# JIRA自助发布主题
			jira_summary = jira.issue(list).fields.summary
			# JIRA自助发布单编号
			jira_key = list
			jira_url = 'http://jira.scm.ppmoney.com/browse/' + str(jira_key)
			# JIRA自助发布项目
			jira_sys = jira.issue(list).fields.customfield_12455.value
			# JIRA自助发布模块
			jira_sys_model = jira.issue(list).fields.customfield_12455.child.value
			# JIRA自助发布类型(HotFix,版本迭代)
			jira_type = jira.issue(list).fields.customfield_10109.value
			# JIRA自助发布版本号
			jira_tag = jira.issue(list).fields.customfield_11104
			# JIRA单创建者
			jira_creator_name = jira.issue(list).fields.creator.name
			jira_creator_displayName = jira.issue(list).fields.creator.displayName
			# JIRA自助发布拖单者
			# jira_user_displayName = jira.issue(list).user.displayName
			jira_user_displayName = jira.issue(list).raw['fields']['creator']['displayName']
			# JIRA自助发布配置格式
			jira_config_type = jira.issue(list).fields.customfield_12203.value
			# JIRA自助发布更新功能
			jira_info = jira.issue(list).fields.customfield_12449
			# JIRA开发审核人
			jira_reviewer_displayName = jira.issue(list).raw['fields']['customfield_10424'][0]['displayName']
			# jira_reviewer_displayName = jira.issue(list).fields.customfield_10424.displayName
			# JIRA格式化时间
			create_time = jira.issue(list).raw['fields']['created']
			create_time = create_time.split('.000')[0].replace('T',' ')
			timeArray = time.strptime(create_time, "%Y-%m-%d %H:%M:%S")
			build_start_time=int(time.mktime(timeArray))
			online_time = int(300)
			build_end_time = build_start_time + online_time
			jira_sql_insert = "INSERT INTO deploy_info  (" \
			                  "Jira_Key,Jira_Sys,Jira_Model,Jira_Tag,Jira_Type,Jira_Creator,Jira_Reviewer,Jira_Summary,Jira_Info,Jira_Url,Jira_Start_Time,Jira_Finish_Time,Jira_Used_Time) " \
			                  "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
			                  (jira_key, jira_sys, jira_sys_model, jira_tag, jira_type, jira_creator_displayName,
			                   jira_reviewer_displayName, jira_summary, jira_info, jira_url, build_start_time,
			                   build_end_time,
			                   online_time)
			print(jira_sql_insert)
			# db.OperateDB().Insert(jira_sql_insert)
# Jira().Other()
