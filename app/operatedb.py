#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/11 16:26
# @Author  : CaiQinYi
# @Site    : 
# @File    : dbexcute.py
# @Software: PyCharm

import pymysql

# Import Custom Model
from conf import settings


class OperateDB(object):
	def __init__(self):
		self.db_host = settings.DB['db_host']
		self.db_user = settings.DB['db_user']
		self.db_pass = settings.DB['db_pass']
		self.db_name = settings.DB['db_name']
		self.db = pymysql.connect(self.db_host,self.db_user,self.db_pass,self.db_name)
		self.cursor = self.db.cursor()

	def Select(self,sql):
		try:
			self.cursor.execute(sql)
			results = self.cursor.fetchall()
			return results
		except:
			self.db.rollback()
		self.db.close()

	def Insert(self,sql):
		try:
			self.cursor.execute(sql)
			self.db.commit()
		except:
			self.db.rollback()
		self.db.close()
	def Update(self,sql):
		try:
			self.cursor.execute(sql)
			self.db.commit()
			# print('sql update' + sql)
		except:
			self.db.rollback()
		self.db.close()

	def Delete(self,sql):
		try:
			self.cursor.execute(sql)
		except:
			self.db.close()