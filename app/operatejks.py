#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/2 12:16
# @Author  : CaiQinYi
# @Site    : 
# @File    : jks.py
# @Software: PyCharm

import collections
import re
import subprocess
import time

import jenkins
import xmltodict

# Import custom model
from conf import settings as sets


#Jenkis 基本信息
class J_Base(object):
	def __init__(self,env):
		self.info = {}
		self.J = jenkins.Jenkins(url=sets.Jks[env]['website'], username=sets.Jks[env]['user'], password=
        sets.Jks[env]['passwd'])

		# 登录用户
		self.login_user = self.J.get_whoami()
		# Jenkins版本
		self.jks_version = self.J.get_version()
		self.jks_jobs_counts = self.J.jobs_count()
		self.jks_views_counts = len(self.J.get_views())
		self.jks_running_builds = len(self.J.get_running_builds())
		self.running_builds = []
		for build in self.J.get_running_builds():
			self.running_builds.append(build['name'])
		self.jks_executor_counts = len(self.J.get_node_info('(master)', depth=0)['executors'])

		self.info['login_user'] = self.login_user
		self.info['jks_version'] = self.jks_version
		self.info['jks_jobs_counts'] = self.J.jobs_count()
		self.info['executor_counts'] = self.jks_executor_counts

	# 欢迎词
	def Welcome(self):
		sets.logger.info('Hello %s, This Jenkins have Jobs count %s, View count %s, Version is %s. ' % \
                             (self.login_user['fullName'], self.jks_jobs_counts, self.jks_views_counts, self.jks_version))

	def Info(self):
		return self.J


class J_Job(object):

	def __init__(self,env):
		self.env = env
		self.J = J_Base(env).Info()

	# 列出Job
	def List(self):
		# Job列表
		for job in self.J.get_jobs():
			sets.logger.info("Job名称：" + job['fullname'] + " Job状态：" + job['color'])
		xml = self.J.get_job_config('demo')

	def Multijobs(self,name):
		# 判断Job类型
		multijobs = []
		multijobs_dict = collections.OrderedDict()
		xml_content = xmltodict.parse(self.J.get_job_config(name))
		for k,v in xml_content.items():
			# 分析Job类型
			job_type = k.split(' ')[0]
			# print(job_type)
			# 自由风格的软件项目，maven项目
			if  job_type == 'project' or job_type == 'maven2-moduleset':
				try:
					# 如该Job下一次构建号为空，则表明它并没有构建过，因此构建号为1
					next_build_number = self.J.get_job_info(name)['nextBuildNumber']
					if next_build_number is None:
						multijobs_dict[name] = 1
					else:
						multijobs_dict[name] = next_build_number
				except Exception as e:
					sets.logger.error(e)
			# 流水线
			elif job_type == 'com.tikal.jenkins.plugins.multijob.MultiJobProject':
				job_lists = xml_content['com.tikal.jenkins.plugins.multijob.MultiJobProject']['builders'][
					'com.tikal.jenkins.plugins.multijob.MultiJobBuilder']['phaseJobs'][
					'com.tikal.jenkins.plugins.multijob.PhaseJobsConfig']
				# Job类型为Multijob，当子Job数量超过一个时，那么子Job返回类型为list，如子Job为1个时，那么它返回类型为OrderedDict
				if isinstance(job_lists,list):
					for job in job_lists:
						if job['jobName'] is not None:
							multijobs.append(job['jobName'])
				elif isinstance(job_lists,dict):
					for k,v in job_lists.items():
						if k == 'jobName' and v is not None:
							multijobs.append(v)
				# 将Job转成有序字典 OrderedDict([('ams_only', 697), ('collect-app', 41)])
				for job in multijobs:
					try:
						# 如该Job下一次构建号为空，则表明它并没有构建过，因此构建号为1
						next_build_number = self.J.get_job_info(job)['nextBuildNumber']
						if next_build_number is None:
							multijobs_dict[job] = 1
						else:
							multijobs_dict[job] = next_build_number
					except Exception as e:
						sets.logger.error(e)
			#匹配成功一次就退出
			break
		return multijobs_dict
	# 创建Job
	def Create(self, name):
		# 复制demo为'empty'配置为空的Job
		self.J.copy_job('demo', name)
		job_config_xml = self.J.get_job_config(name)
		Git_Url = str(input('Plase Input Git Url: '))
		Git_Type = str(input('Plase Input Git Type(Branch|Tag): '))
		Maven_Parameter = str(input('Plase Input Maven Parameter: '))
		try:
			self.J.create_job(name, jenkins.EMPTY_CONFIG_XML)
		except Exception as e:
			sets.logger.warning(e)
		pass

	# 配置Job
	def Config(self, name, operate=None):
		if operate == 'enable':
			self.J.enable_job(name)
		if operate == 'disable':
			self.J.disable_job(name)
		if operate == 'delete':
			self.J.delete_job(name)

	# 检查Job
	def Check(self, *args):
		# 检查Job是否存在，预发布不存在Jobs则提醒并默认跳过
		if args[0] == 'Job':
			try:
				if self.J.job_exists(args[1]):
					return True, '{0} 存在'.format(args[1])
				elif self.env == 'Staging':
					return False, '预发布环境未接入 {0}，默认跳过构建'.format(args[1])
				elif self.env == 'Prod':
					return False, '{0} 不存在，请联系运维 '.format(args[1])
			except Exception as e:
				sets.logger.error(str(e))
		# 检查Tag版本
		if args[0] == 'Tag':
			# Option Tag Job_Name Tag_Value
			results = {}
			multijobs_dict = self.Multijobs(args[1])
			for job,job_value in multijobs_dict.items():
				xml_content = xmltodict.parse(self.J.get_job_config(job))
				git_branch = ''
				git_registry= ''
				for k,v in xml_content.items():
					if 'project' in k:
						try:
							git_registry = xml_content['project']['scm']['userRemoteConfigs']['hudson.plugins.git.UserRemoteConfig']['url']
							git_branch = xml_content['project']['scm']['branches']['hudson.plugins.git.BranchSpec']['name']
						except Exception as e:
							sets.logger.error(str(e))
							git_registry = ''

					elif 'maven2-moduleset' in k:
						try:
							git_registry = xml_content['maven2-moduleset']['scm']['userRemoteConfigs']['hudson.plugins.git.UserRemoteConfig']['url']
							git_branch = xml_content['maven2-moduleset']['scm']['branches']['hudson.plugins.git.BranchSpec']['name']
						except Exception as e:
							sets.logger.error(str(e))
							git_registry = ''
							git_branch = ''
					break
				# 排除空git_registry
				if git_registry != '':
					#判断git仓库是否变量，如有则使用传过来的参数，如无则使用Job中指定的参数
					if 'branch' in git_branch:
						check_tag = '{0} ls-remote -h -t {1}|grep "{2}$" '.format(sets.System['gitpath'], git_registry, args[2])
					else:
						git_branch = ''.join(re.findall('[a-z]',git_branch))
                        check_tag = '{0} ls-remote -h -t {1}|grep "/{2}$" '.format(sets.System['gitpath'], git_registry, git_branch)
					sets.logger.info(check_tag)
					check_tag_result = subprocess.getstatusoutput(check_tag)[0]
					results[job] = check_tag_result
					# if check_tag_result == 0:
					# 	results[job] = {git_registry:args[2]}
					# else:
					# 	sets.logger.error('Tag no exit' + check_tag)
					# 	break
				else:
					results[job] = 0
					continue
			#如果所有的项目检查都通过，那么则返回结果
			result_text = ''
			fail_count = 0
			for k,v in results.items():
				if v == 0:
					result_text = result_text  + '通过：{0}'.format(k) + '  \n'
				else:
					result_text = result_text + '不通过：{0}'.format(k) + '  \n'
					fail_count = fail_count + 1
			if fail_count == 0:
				return True,result_text
			else:
				return False,result_text

	# 构建Job
	def Build(self, name, build_dict,jira_log):
		multijobs_dict = self.Multijobs(name)
		try:
			# 如该Job下一次构建号为空，则表明它并没有构建过，因此构建号为1
			if self.J.get_job_info(name)['nextBuildNumber'] is None:
				next_build_number = 1
			else:
				next_build_number = self.J.get_job_info(name)['nextBuildNumber']
			# 构建带有参数的Job
			self.J.build_job(name, build_dict)
			# Jenkins默认5秒等到时间，这个参数在系统设置中的 Quiet period 可获取。
			time.sleep(8)
			# 设置等待时间
			sleep_time = 0
			while True:
				try:
					# 如next_build_number可正常获取构建信息则表示该构建号存在
					self.J.get_build_info(name, next_build_number)
					break
				except Exception as e:
					if 'does not exist' in str(e):
						if sleep_time<=100:
							time.sleep(6)
							sleep_time = sleep_time + 1
						# 如等到超过一分钟还报构建号不存在，则返回错误代码
						else:
							return False, str(e)
					else:
						sets.logger.info(name + 'build FAILURE')
						return False, str(e)
			build_info = self.J.get_build_info(name, next_build_number)
			sets.logger.debug(build_info)
			build_result = build_info['result']
			# 当构建结果为None时，则表示Job依旧在构建
			while build_result is None:
				# 循环取出主Job中嵌入的子Job  OrderedDict([('ams_only', 697), ('collect-app', 41)])
				for k,v in multijobs_dict.items():
					while True:
						try:
							# job_build_result 中result可整获取，则表示该jobs已经在运行，调到获取子jobs日志点
							job_build_result = self.J.get_build_info(k, v)['result']
							break
						except Exception as e:
							if 'does not exist' in str(e):
								time.sleep(6)
								if sleep_time <= 100:
									sleep_time = sleep_time + 1
								# 如等到超过十分钟还报构建号不存在，则返回错误代码
								else:
									return False, str(e)
							else:
								sets.logger.info(name + 'build FAILURE')
								return False, str(e)
					while job_build_result is None:
						build_console_output = self.J.get_build_console_output(k, v)
						hostname_list = re.findall(r'\baz-\S*?.local\b',build_console_output)
						for hostname in hostname_list:
							build_console_output = build_console_output.replace(hostname,'**隐藏主机名**')
						job_build_result = self.J.get_build_info(k, v)['result']
						# with open(jira_log, 'w+', encoding='utf-8') as f:
						with open(jira_log, 'w+', encoding='GB2312') as f:
							f.write(build_console_output)
						time.sleep(0.5)
					if job_build_result != 'SUCCESS':
						break
				# 子Job跑完后，主Job的结果并不那么快获取。
				build_result = self.J.get_build_info(name, next_build_number)['result']
				while build_result is None:
					build_result = self.J.get_build_info(name, next_build_number)['result']
					time.sleep(1)
			sets.logger.info(build_info)
			build_console_output = self.J.get_build_console_output(name, next_build_number)
			if build_result == 'SUCCESS':
				sets.logger.info(name + ' build SUCCESS')
				return True
				# return (True, build_console_output.replace('>>', '\>>'))
			elif build_result == 'FAILURE' or build_result == 'ABORTED':
				sets.logger.info(name + ' build FAILURE')
				return False
				# return (False, build_console_output.replace('>>', '\>>'))
		except Exception as e:
			sets.logger.error(e)
			return False, str(e)

	def Delete(self, name):
		pass

# Jenkins 视图相关
class J_View(object):
	def __init__(self,env):
		self.J = J_Base(env).Info()

	def List(self):
		# 获取视图下所有job列表
		jobs = self.J.get_jobs(view_name='Sit_yqh')
		pass

	def Create(self):
		# 创建视图
		try:
			self.J.create_view('EMPTY', jenkins.EMPTY_VIEW_CONFIG_XML)
		except Exception as e:
			sets.logger.warning(e)
		view_config = self.J.get_view_config('EMPTY')
		pass

	def Config(self):
		# 删除视图
		self.J.delete_view('EMPTY')
		views = self.J.get_views()
		# print([view['name'] for view in views])
		pass

# 三种类型Job
# J_Job('Staging').Multijobs('nirvana-iam') 				#自由风格的软件项目
# print(J_Job('Staging').Multijobs('SHRL_dev'))					#moven项目
# J_Job('Staging').Multijobs('baozi-ssq-file-server')		#流水线

# print(J_Job('Staging').Check('Tag','SHRL_arceus-server-chjtest','v0.0.4.2019040301'))
# print(J_Base('Prod').Welcome())
# J_Job('Staging').Check('Job', 'SHRL_dev1')
