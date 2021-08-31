#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/2 14:23
# @Author  : CaiQinYi
# @Site    : 
# @File    : manage.py
# @Software: PyCharm

'''
#C:\Python36\Scripts\pipreqs.exe ./ --encoding=utf8 --force
'''
import sys
import os
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web


# Import custom model
from app import main
from conf import settings as sets

def run_api():
	'''启动Jira参数监听'''
	if not os.path.exists(sets.Jks['home']):
		os.mkdir(sets.Jks['home'])
	tornado.options.parse_command_line()
	app = tornado.web.Application(handlers=[(r"/", main.IndexHandler)],
								  static_path='static',
								  autoreload=True,
								  debug=False)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(sets.System['api_port'])
	tornado.ioloop.IOLoop.instance().start()

def run_log():
	'''启动错误日志监听'''
	tornado.options.parse_command_line()
	app = tornado.web.Application(handlers=[(r"/", main.IndexHandler)], static_path='tmp', debug=False)
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(sets.System['log_port'])
	tornado.ioloop.IOLoop.instance().start()

usage = '''
usage: manage.py [-h] [run_api] [run_log]

Process some publish request.

optional arguments:
 -h, --help  show this help message and exit
 run_api        Start Api Interface And Execute Jira Publish Message Which Build Remote Jenkins.
 run_log        Provides Jenkins Console text logs When Build Failure.
'''

try:
	cmd = sys.argv[1]
	if cmd == 'run_api':
		run_api()
	# daemon_runner = runner.DaemonRunner(run_api())
	# This ensures that the logger file handle does not get closed during daemonization
	# daemon_runner.daemon_context.files_preserve = [handler.stream]
	# daemon_runner.do_action()

	elif cmd == 'run_log':
		# daemon_runner = runner.DaemonRunner(app)
		# This ensures that the logger file handle does not get closed during daemonization
		# daemon_runner.daemon_context.files_preserve = [handler.stream]
		# daemon_runner.do_action()
		run_log()
	elif cmd == '-h':
		print(usage)
	else:
		print(usage)
except Exception as e:
	print(usage)
