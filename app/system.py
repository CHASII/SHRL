#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/2 14:22
# @Author  : CaiQinYi
# @Site    : 
# @File    : system.py
# @Software: PyCharm

import os
import socket
import subprocess
import shlex

# Import Custom Model
from conf import settings


# iface参数指Linux的网卡接口，如(eth0,wlan0)，这个参数只支持Linux并且需要root权限


def freeport(iface=None):
	"获取随机空闲端口"
	SO_BINDTODEVICE = 25
	s = socket.socket()
	if iface:
		s.setsockopt(socket.SOL_SOCKET, SO_BINDTODEVICE, bytes(iface, 'utf8'))
	s.bind(('', 0))
	port = s.getsockname()[1]
	s.close()
	settings.logger.info('Get System FreePort {0}'.format(port))
	return port


def webtail(tailpath,listen_port,logfile,jira_key):
	"输出Jenkins实时日志"
	try:
		if not os.path.exists(logfile):
			os.mknod(logfile)
		command = '{0} {1} {2} {3} {4}'.format(settings.System['pythonpath'], tailpath, listen_port, logfile, jira_key)
		args = shlex.split(command)
		p = subprocess.Popen(args)
		return p.pid
	except Exception as e:
		settings.logger.error(str(e))


def operate(operate_type,operate_object):
	"删除文件、杀死进程"
	if operate_type == 'remove_file':
		try:
			os.remove(operate_object)
		except Exception as e:
			settings.logger.error(e)
	if operate_type == 'kill_process':
		try:
			os.system('kill -9 {0}'.format(operate_object))
		except Exception as e:
			settings.logger.error(e)