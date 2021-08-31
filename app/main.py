#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/1/2 12:17
# @Author  : CaiQinYi
# @Site    : 
# @File    : socket.py
# @Software: PyCharm

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor

import tornado.gen
import tornado.web
from tornado.concurrent import run_on_executor

# Import custom model
from app import system, operatejks as jks, operatecfg as cfg, message, operatedb as db
from conf import settings as sets


class IndexHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(50)

    @tornado.gen.coroutine
    def get(self):
        html_context = '<h3>Hi,Guy：</h3> <h4>This is Webhook For JiraJks by PPmoney OPS！If you has any qestions please contact <a href=mailto:caiqinyi@ppmoney.com">caiqinyi@ppmoney.com</a>,Tks!</h4>'
        self.write(html_context)

    @tornado.gen.coroutine
    def post(self):
        data = json.loads(self.request.body)
        sets.logger.info(json.dumps(data,indent=4))
        self.Analyse(data)

    @run_on_executor
    def Analyse(self, data):
        for item in data['changelog']['items']:
            if str(item['fromString']) != 'None' and str(item['toString']) != 'None':
                # Jira自助发布创建者
                # jira_creator = data['issue']['fields']['creator']['displayName']
                # Jira自助发布主题
                jira_summary = data['issue']['fields']['summary']
                # Jira自助发布单编号
                jira_key = data['issue']['key']
                jira_url = sets.Jira['host'] + '/browse/' + jira_key
                # 定义Jenkins构建console
                jira_log = os.path.join(sets.Jks['home'], jira_key) + '.js'
                # jira_log = os.path.join(sets.Jks['home'], jira_key)
                # Jira自助发布项目
                jira_sys = data['issue']['fields']['customfield_12455']['value']
                # Jira自助发布模块
                jira_sys_model = str(data['issue']['fields']['customfield_12455']['child']['value']).replace(' ', '')
                # Jira自助发布类型(HotFix,版本迭代)
                jira_type = data['issue']['fields']['customfield_10109']['value']
                # Jira自助发布版本号
                jira_tag = str(data['issue']['fields']['customfield_11104']).replace(' ', '')
                # Jira单创建者
                # jira_creator_name = data['issue']['fields']['creator']['name']
                jira_creator_displayName = data['issue']['fields']['creator']['displayName']
                # Jira自助发布拖单者
                # jira_user_name = data['user']['name']
                jira_user_displayName = data['user']['displayName']
                # Jira自助发布配置格式
                # jira_config_type = data['issue']['fields']['customfield_12203']['value']
                # Jira自助发布更新功能
                jira_info = data['issue']['fields']['customfield_12449']

                dingtalk_msg = "**Env-{build_env} | Build-{build_status}**  \n" \
                               "- - -   \n" \
                               "发布主体  \n" \
                               "> 编号：[%s](%s)  \n" \
                               "标题：%s   \n" \
                               "项目：%s  \n" \
                               "模块：%s    \n" \
                               "标签：%s  \n" % (jira_key, jira_url, jira_summary, jira_sys, jira_sys_model, jira_tag)
                dingtalk_msg_single = "**Env-{build_env} | Build-{build_status}**  \n" \
                                      "- - -  \n" \
                                      "发布主体  \n" \
                                      "> 编号：[%s](%s)   \n" \
                                      "标题：%s  \n" \
                                      "模块：%s  \n" % (jira_key, jira_url, jira_summary, jira_sys_model)
                if item['field'] == 'status' and item['toString'] != '已完成(待归档)':
                    change_time = time.strftime('%m.%d %H:%M', time.localtime())
                    change_log = change_time + jira_user_displayName + ' move ' + "[{0}]({1})".format(jira_key,
                                                                                                      jira_url) + ' from ' + \
                                 item['fromString'] + ' to ' + item['toString'] + '  \n'
                    sets.logger.info(change_log)
                    message.write_msg(jira_log + '_transition', change_log)
                    # 过滤预发布及生产环节
                    if item['fieldtype'] == 'jira' and (item['toString'] == u'预发布环节' or item['toString'] == u'生产环节'):
                        # Jira单测试负责人
                        jira_reviewer_displayName = data['issue']['fields']['customfield_10424'][0]['displayName']
                        # Jira泳道名称
                        jira_transitions_name = str(item['toString'])
                        if jira_transitions_name == u'预发布环节':
                            sys_env = 'Staging'
                        else:
                            sys_env = 'Prod'
                        sets.logger.info('自助发布进入 {0}'.format(sys_env))


                        # ---------------PrePared
                        msg_content = dingtalk_msg_single.format(build_env=sets.Color[sys_env], build_status=sets.Color['Prepare'])
                        # 收集报错信息
                        Error_Msg = []
                        # 判断是否更新配置
                        stag_config_content = ''
                        prod_config_content = ''
                        sets.logger.info('Trying to Get Whether Need to Add or Update Application Config')
                        # 配置格式
                        applicaiton_config_type = data['issue']['fields']['customfield_12534']['value']
                        # 配置目录
                        try:
                            application_config_dir = data['issue']['fields']['customfield_12531'].replace(' ', '')
                        except Exception as e:
                            application_config_dir = ''
                            sets.logger.warning(str(e))
                        # 获取配置变更的应用目录及配置内容
                        if applicaiton_config_type != u'无':
                            if application_config_dir != '':
                                try:
                                    jira_sql_select = "SELECT  cfg_dir from cfg_info where jira_model = '{0}'".format(jira_sys_model)
                                    jira_sql_result = db.OperateDB().Select(jira_sql_select)
                                    if jira_sql_result is None or len(jira_sql_result) == 0 or jira_sql_result[0][0] != application_config_dir:
                                        Error_Msg.append("{0}".format(sets.Error_Code['配置类']['01']))
                                    else:
                                        try:
                                            stag_config_content = data['issue']['fields']['customfield_12528']
                                            sets.logger.debug('application_config_dir {0}'.format(application_config_dir))
                                            sets.logger.debug('stag_config_content {0}'.format(stag_config_content))
                                        except Exception as e:
                                            sets.logger.error(str(e))
                                        try:
                                            prod_config_content = data['issue']['fields']['customfield_12529']
                                            sets.logger.debug('application_config_dir {0}'.format(application_config_dir))
                                            sets.logger.debug('prod_config_content {0}'.format(prod_config_content))
                                        except Exception as e:
                                            sets.logger.error(str(e))

                                except Exception as e:
                                    sets.logger.error(str(e))
                            else:
                                Error_Msg.append("{0}".format(sets.Error_Code['配置类']['03']))

                        # 判断环境及配置内容是否为空
                        if sys_env == 'Staging':
                            # 检查Job是否存在
                            Job_Check_Status, Job_Check_Result = jks.J_Job(sys_env).Check('Job', jira_sys_model)
                            if not Job_Check_Status:
                                # msg_content = dingtalk_msg_single.format(build_env=sets.Color[sys_env], build_status=sets.Color['Prepare'])
                                msg_content = msg_content + '\n- - -  \n温馨提示  \n' + '> {0}  \n'.format(str(Job_Check_Result))
                                # msg_content = msg_content + '\n- - -  \n温馨提示  \n' + '> <font color=#dd0000>{0}'.format(str(Job_Check_Result)) + '</font>'
                                try:
                                    message.send_dingtalk(jira_sys, msg_content)
                                except Exception as e:
                                    sets.logger.warning(e)
                                break
                            else:
                                try:
                                    message.send_dingtalk(jira_sys, msg_content)
                                except Exception as e:
                                    sets.logger.warning(e)

                            # ---Prepare
                            # 检查Tag
                            sets.logger.info('Starting to Check Tag %s %s' % (jira_sys_model, jira_tag))
                            try:
                                Tag_Check_Status, Tag_Check_Result = jks.J_Job(sys_env).Check('Tag', jira_sys_model, jira_tag)
                                msg_content = '\n- - -  \n标签检查  \n> {}  \n'.format(Tag_Check_Result)
                                if not Tag_Check_Status:
                                    Error_Msg.append(sets.Error_Code['仓库类']['01'])
                            except Exception as e:
                                Error_Msg.append(sets.Error_Code['仓库类']['02'])
                                sets.logger.error(str(e))
                                break

                            sets.logger.info('Try to update {0} config'.format(sys_env))
                            if application_config_dir != '' and applicaiton_config_type != u'无' and stag_config_content != '' and stag_config_content is not None:
                                if applicaiton_config_type == 'properties':
                                    try:
                                        Cfg_Update_Status, Cfg_Update_Result = cfg.OperateCfg(sys_env).Analyse(sets.GitLab[sys_env]['repository_name'],
                                                                                                               application_config_dir,
                                                                                                               applicaiton_config_type, stag_config_content,
                                                                                                               str(jira_key) + ' ' + str(jira_summary))
                                        if not Cfg_Update_Status:
                                            Error_Msg.append("{0} {1}".format(application_config_dir, Cfg_Update_Result))
                                        else:
                                            msg_content = msg_content + '\n- - -  \n配置变更  \n>名称：{0}  \n状态：{1}  \n'.format(application_config_dir,
                                                                                                                          Cfg_Update_Result)
                                    except Exception as e:
                                        sets.logger.error(str(e))
                                        Error_Msg.append(sets.Error_Code['仓库类']['02'])
                                else:
                                    Error_Msg.append(sets.Error_Code['配置类']['02'])

                        elif sys_env == 'Prod':

                            # else:
                            #     try:
                            #         message.send_dingtalk(jira_sys, msg_content)
                            #     except Exception as e:
                            #         sets.logger.warning(e)

                            # 检查Job
                            Job_Check_Status, Job_Check_Result = jks.J_Job(sys_env).Check('Job', jira_sys_model)
                            if not Job_Check_Status:
                                msg_content = dingtalk_msg_single.format(build_env=sets.Color[sys_env], build_status=sets.Color['Prepare'])
                                msg_content = msg_content + '\n- - -  \n错误信息  \n' + '> <font color=#dd0000>{0}</font>  \n'.format(Job_Check_Result)
                                try:
                                    message.send_dingtalk(jira_sys, msg_content)
                                except Exception as e:
                                    sets.logger.warning(e)
                                break
                            else:
                                # 检查是否预约
                                # 检查是否预约
                                appoint_time = ''
                                build_start_time = ''
                                try:
                                    appoint_time = data['issue']['fields']['customfield_12526'].split('.000')[0].replace('T', ' ')
                                    build_start_time = int(time.mktime(time.strptime(appoint_time, "%Y-%m-%d %H:%M:%S")))
                                except Exception as e:
                                    sets.logger.error(str(e))
                                if appoint_time:
                                    sleep_time = build_start_time - time.time()
                                    if 0 < sleep_time / 60 <= 60:
                                        sets.logger.info("自助进入预约模式，预计 {0} 开始".format(appoint_time))
                                        msg_content = msg_content + '\n- - -  \n预约上线  \n>时间： {}  \n'.format(appoint_time)
                                        try:
                                            message.send_dingtalk(jira_sys, msg_content)
                                        except Exception as e:
                                            sets.logger.warning(e)
                                        time.sleep(sleep_time - 6)
                                    else:
                                        msg_content = msg_content + '\n- - -  \n预约上线  \n>时间： {}  \n'.format(
                                            appoint_time) + '\n- - -  \n错误信息  \n' + '> <font color=#dd0000>时间选错(上午|下午)或超过限制时长(1小时)</font>  \n'
                                        try:
                                            message.send_dingtalk(jira_sys, msg_content)
                                            break
                                        except Exception as e:
                                            sets.logger.warning(e)

                            #### --Started
                            # 检查Tag
                            sets.logger.info('Starting to Check Tag %s %s' % (jira_sys_model, jira_tag))
                            try:
                                Tag_Check_Status, Tag_Check_Result = jks.J_Job(sys_env).Check('Tag', jira_sys_model, jira_tag)
                                msg_content = '\n- - -  \n标签检查  \n> {}  \n'.format(Tag_Check_Result)
                                if not Tag_Check_Status:
                                    Error_Msg.append(sets.Error_Code['仓库类']['01'])
                            except Exception as e:
                                Error_Msg.append(sets.Error_Code['仓库类']['02'])
                                sets.logger.error(str(e))
                                break

                            sets.logger.info('Try to update {0} config'.format(sys_env))
                            if application_config_dir != '' and applicaiton_config_type != u'无' and prod_config_content != '' and prod_config_content is not None:
                                if applicaiton_config_type == 'properties':
                                    try:
                                        Cfg_Update_Status, Cfg_Update_Result = cfg.OperateCfg(sys_env).Analyse(
                                            sets.GitLab[sys_env]['repository_name'], application_config_dir,
                                            applicaiton_config_type, prod_config_content, jira_key + ' ' + jira_summary)
                                        # msg_content = msg_content + '\n- - -  \n配置变更  \n>名称：{0}  \n状态：{1}  \n'.format(
                                        #     application_config_dir, Cfg_Update_Result)
                                        if not Cfg_Update_Status:
                                            Error_Msg.append("{0} {1}".format(application_config_dir, Cfg_Update_Result))
                                        else:
                                            msg_content = msg_content + '\n- - -  \n配置变更  \n>名称：{0}  \n状态：{1}  \n'.format(
                                                application_config_dir, Cfg_Update_Result)
                                    except Exception as e:
                                        sets.logger.error(str(e))
                                        Error_Msg.append(sets.Error_Code['仓库类']['02'])
                                else:
                                    Error_Msg.append(Error_Msg.append(sets.Error_Code['配置类']['02']))

                        # 判断是否有错误信息
                        if Error_Msg:
                            msg_content = dingtalk_msg.format(build_env=sets.Color[sys_env],build_status=sets.Color[
                                'Failure']) + '\n- - -  \n错误信息  \n' + '> <font color=#dd0000>{0}</font>  \n'.format('  \n'.join(Error_Msg))
                            try:
                                message.send_dingtalk(jira_sys, msg_content)
                            except Exception as e:
                                sets.logger.warning(e)
                            break

                        # 获取随机端口号
                        sets.logger.info('Starting to get system freeport')
                        build_console_port = system.freeport()
                        build_console_url = str(sets.System[sys_env]['localip']) + ':' + str(build_console_port)

                        # 获取Pid进程号
                        root_path = os.path.dirname(os.path.abspath(__file__))
                        webtail_pid = system.webtail(os.path.join(root_path, 'webtail.py'), build_console_port, jira_log, jira_key)
                        # 初始化消息推送次数避免重复推送
                        message_send_counts = 0
                        # Jenkins默认5秒等到时间，这个参数在系统设置中的 Quiet period 可获取。
                        time.sleep(8)
                        # 判断是否有空闲队列构建
                        while jks.J_Base(sys_env).jks_running_builds >= jks.J_Base(sys_env).jks_executor_counts:
                            msg_content = dingtalk_msg_single.format(build_env=sets.Color[sys_env],build_status=sets.Color[
                                'Prepare']) + "\n- - -  \n温馨提醒  \n>当前有{0}等{1}个Jobs在运行,已达系统上限,请耐心等待...  \n".format(
                                jks.J_Base(sys_env).running_builds, jks.J_Base(sys_env).jks_executor_counts)
                            # 等待过程限制只推送一次消息
                            if message_send_counts == 0:
                                message.send_dingtalk(jira_sys, msg_content)
                                message_send_counts = message_send_counts + 1
                            time.sleep(30)

                        # 获取近期迭代
                        recent_update_sql = "select Jira_Summary,Jira_Finish_Time from deploy_info where Jira_Model='{0}' ORDER BY id  DESC limit {1}".format(
                            jira_sys_model, sets.System['publish_record'])
                        recent_update_result = db.OperateDB().Select(recent_update_sql)
                        sets.logger.debug(recent_update_result)
                        recent_update_result_list = []

                        # 获取该项目是否有更新记录
                        if recent_update_result is None or len(recent_update_result) == 0:
                            sets.logger.error(recent_update_result)
                        else:
                            for row in recent_update_result:
                                Jira_Summary = row[0]
                                Jira_Online_Time = row[1]
                                try:
                                    ltime = time.localtime(int(Jira_Online_Time))
                                    Jira_Online_Time = time.strftime("%m.%d %H:%M", ltime)
                                    recent_update_result_list.append(
                                        "[{0}] {1}  \n".format(Jira_Online_Time, Jira_Summary))
                                except Exception as e:
                                    sets.logger.error(e)
                        recent_update = ''.join(recent_update_result_list)
                        msg_content = msg_content + "\n- - -  \n实时状态  \n> 日志：[Console]({0})  \n".format(
                            build_console_url) + "\n- - -  \n迭代记录  \n> {0}  \n".format(recent_update)
                        msg_content = dingtalk_msg.format(build_env=sets.Color[sys_env], build_status=sets.Color['Started']) + msg_content
                        try:
                            message.send_dingtalk(jira_sys, msg_content)
                        except Exception as e:
                            sets.logger.warning(e)

                        # ---------------Finished
                        # 上线开始时间
                        build_start_time = int(time.time())
                        # 构建Jenkins
                        build_status = jks.J_Job(sys_env).Build(str(jira_sys_model).replace(' ', ''), {"branch": str(jira_tag).replace(' ', '')}, jira_log)
                        build_log = '[点此查看失败日志]({0})'.format(sets.System[sys_env]['localip'] + ':' + sets.System['log_port'] + '/static/' + jira_key + '.js')
                        # 上线结束时间
                        build_end_time = int(time.time())
                        # 总上线时间-秒
                        online_time = build_end_time - build_start_time
                        # 总上线时间-分
                        # online_time_min = round((build_end_time - build_start_time) / 60 + 1)
                        # 如果构建成功则返回True
                        if build_status:
                            msg_content = dingtalk_msg_single.format(build_env=sets.Color[sys_env],
                                                                     build_status=sets.Color['Success'])
                            jira_sql_select = "SELECT * from deploy_info where Jira_Key = '{0}'".format(jira_key)
                            jira_sql_insert = "INSERT INTO deploy_info  (" \
                                              "Jira_Key,Jira_Sys,Jira_Model,Jira_Tag,Jira_Type,Jira_Creator,Jira_Reviewer,Jira_Summary,Jira_Info,Jira_Url,Jira_Start_Time,Jira_Finish_Time,Jira_Used_Time) " \
                                              "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                                              (
                                                  jira_key, jira_sys, jira_sys_model, jira_tag, jira_type,
                                                  jira_creator_displayName, jira_reviewer_displayName, jira_summary,
                                                  jira_info,
                                                  jira_url, build_start_time, build_end_time, online_time)
                            jira_sql_update = "UPDATE deploy_info  (" \
                                              "Jira_Key,Jira_Sys,Jira_Model,Jira_Tag,Jira_Type,Jira_Creator,Jira_Reviewer,Jira_Summary,Jira_Info,Jira_Url,Jira_Start_Time,Jira_Finish_Time,Jira_Used_Time) " \
                                              "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % \
                                              (
                                                  jira_key, jira_sys, jira_sys_model, jira_tag, jira_type,
                                                  jira_creator_displayName, jira_reviewer_displayName, jira_summary,
                                                  jira_info,
                                                  jira_url, build_start_time, build_end_time, online_time)
                            # 读取变更记录插入数据库
                            with open(jira_log + '_transition', mode='r') as f:
                                change_log = ''.join(f.readlines())
                                insert_jira_log = 'update  deploy_info set Jira_Log = "{Jira_Log}"  WHERE Jira_Key = "{Jira_Key}"'.format(
                                    Jira_Log=change_log, Jira_Key=jira_key)
                            try:
                                message.send_dingtalk(jira_sys, msg_content)
                                # 插入数据库
                                jira_sql_result = db.OperateDB().Select(jira_sql_select)
                                # 查询数据库，如该Jira单号不存在则插入，如存在则更新数据库
                                if jira_sql_result is None or len(jira_sql_result) == 0:
                                    db.OperateDB().Insert(jira_sql_insert)
                                    db.OperateDB().Update(insert_jira_log)
                                else:
                                    db.OperateDB().Update(jira_sql_update)
                                    db.OperateDB().Update(insert_jira_log)
                            except Exception as e:
                                sets.logger.warning(e)
                            try:
                                message.send_mail(sys_env, jira_summary, jira_info)
                            except Exception as e:
                                sets.logger.warning(e)
                        else:
                            msg_content = dingtalk_msg_single.format(build_env=sets.Color[sys_env],build_status=sets.Color[
                                'Failure']) + '\n- - -  \n错误信息  \n' + '> <font color=#dd0000>{0}</font>  \n'.format(build_log)
                            try:
                                message.send_dingtalk(jira_sys, msg_content)
                            except Exception as e:
                                sets.logger.warning(e)
                            # 如上线失败则沉默一段时候再将console关闭
                            time.sleep(1800)
                        # 杀死进程及删除构建本地日志
                        system.operate('kill_process', webtail_pid)
                        if sys_env == u'生产环节':
                            system.operate('remove_file', os.path.join(jira_log))
                        system.operate('remove_file', jira_log + '_transition')
                # 完成归档通知无需发送
                elif item['toString'] != '已完成(待归档)':
                    try:
                        change_time = time.strftime('%m.%d %H:%M', time.localtime())
                        change_log = change_time + jira_user_displayName + ' move ' + "[{0}]({1})".format(jira_key, jira_url) + ' from ' + \
                                     item['fromString'] + ' to ' + item['toString'] + '  \n'
                        sets.logger.info(change_log)
                        message.write_msg(jira_log + '_transition', change_log)
                    except Exception as e:
                        sets.logger.warning(e)