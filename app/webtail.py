#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/2 12:19
# @Author  : CaiQinYi
# @Site    : 
# @File    : webtail.py
# @Software: PyCharm

from tornado.web import Application
from tornado.web import RequestHandler
import tornado.ioloop
import tornado.httpserver
from tornado.websocket import WebSocketHandler
import os
import sys

# Import custom model
from conf import settings as sets

# 监听端口
http_port = sys.argv[1]
log_file = sys.argv[2]
jira_key = sys.argv[3]

def create_app():
	handlers = [(r"/", IndexHandler), (r'/show', CommandHandler)]
	app = Application(
		handlers=handlers, static_path='static',debug=True, cookie_secret='asdadasdadasdasdasda')
	return app

class IndexHandler(RequestHandler):
	def get(self):
		self.render(os.path.join('../templates','index.html'),REQUEST_HOST=self.request.host,JIRA_KEY=jira_key)

class CommandHandler(WebSocketHandler):
	def open(self):
		sets.logger.info("WebSocket opened")
		LISTENERS.append(self)
	def on_message(self, message):
		pass
	def on_close(self):
		sets.logger.info("WebSocket closed")
		try:
			LISTENERS.remove(self)
		except:
			pass

def tail_file():
	where = stdout_file.tell()
	line = stdout_file.readline()
	if not line:
		stdout_file.seek(where)
	else:
		for element in LISTENERS:
			element.write_message('stdout:{}'.format(line))

if __name__ == '__main__':
	LISTENERS = []
	log_file = os.path.abspath(log_file)
	# stdout_file = open(log_file, encoding='utf-8')
	stdout_file = open(log_file, encoding='utf-8')
	stdout_file.seek(os.path.getsize(log_file))
	app = create_app()
	http_server = tornado.httpserver.HTTPServer(app)
	http_server.listen(http_port, '0.0.0.0')
	tailed_callback = tornado.ioloop.PeriodicCallback(tail_file, 10)
	tailed_callback.start()
	io_loop = tornado.ioloop.IOLoop.instance()
	try:
		io_loop.start()
	except SystemExit as KeyboardInterrupt:
		io_loop.stop()
		stdout_file.close()