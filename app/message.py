#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/2 12:14
# @Author  : CaiQinYi
# @Site    : 
# @File    : message.py
# @Software: PyCharm

import json
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import requests

# Import custom model
from conf import settings


def send_dingtalk(title, text):
	headers = {'Content-Type': 'application/json'}
	send_data = {
		"msgtype": "markdown",
		"at": {
			"isAtAll": 'false',
		},
		"markdown": {
			"title": title,
			"text": text + '  \n###### {}推送'.format(time.strftime("%Y.%m.%d %H:%M:%S",time.localtime()))
		}
	}
	for name, token in settings.DingTalk.items():
		Api_Url: str = 'https://oapi.dingtalk.com/robot/send?access_token={0}'.format(token)
		settings.logger.info('开始推送钉钉消息')
		settings.logger.debug('钉钉消息 :\n' + text)
		resp = 'unknown'
		try:
			time.sleep(random.randint(2, 5))
			resp = requests.post(url=Api_Url, headers=headers, data=json.dumps(send_data)).text
		except Exception as e:
			time.sleep(3)
			settings.logger.error(str(e))
			try:
				resp = requests.post(url=Api_Url, headers=headers, data=json.dumps(send_data)).text
			except Exception as e:
				settings.logger.error(str(e))
			settings.logger.info('推送结果 :' + resp)
			time.sleep(1)

def send_mail(env,subject, content):
	if env == 'Prod':
		msg = MIMEMultipart()
		now = time.strftime('%Y/%m/%d %H:%M', time.localtime(time.time()))
		msg['Subject'] = "自助发布: " + subject + '[' + now + ']'  # 标题
		msg['From'] = settings.Email['sender_nickname']  # 发件人昵称
		msg['To'] = settings.Email['receiver_nickname']  # 收件人昵称
		# 正文-图片 只能通过html格式来放图片，所以要注释25，26行
		mail_msg = content
		# msg.attach(MIMEText(mail_msg, 'html', 'utf-8'))
		msg.attach(MIMEText(mail_msg, 'plain', 'utf-8'))

		# 发送
		try:
			smtp = smtplib.SMTP()
			smtp.connect(settings.Email['sender_host'], 25)
			smtp.login(settings.Email['sender_name'], settings.Email['sender_password'])
			smtp.sendmail(settings.Email['sender_name'], settings.Email['receiver_name'], msg.as_string())
			smtp.quit()
			settings.logger.info('开始发送邮件消息')
			settings.logger.debug('邮件消息 :\n' + '标题 : \n' + subject + '内容 \n' + content)
			settings.logger.info('邮件发送成功')
			return True
		except Exception as e:
			settings.logger.error('send mail msg {}'.format(e))
			return False

def write_msg(filename,msg):
	try:
		with open(filename,mode='a+') as f:
			f.write(msg)
	except Exception as e:
		settings.logger.error(str(e))