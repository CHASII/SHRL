#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/2/27 16:09
# @Author  : CaiQinYi
# @Site    : 
# @File    : operatecfg.py
# @Software: PyCharm

'''
https://blog.csdn.net/mooncrystal123/article/details/85100903
https://python-gitlab.readthedocs.io/en/stable/install.html
如有：gitlab.exceptions.GitlabHttpError: 404: 404 File Not Found
1.token不对，可能需使用创建该项目的用户生成
2.文件名前缀有误，可能存在空格
3.重新生成
'''
import gitlab
import time
import collections
import re
import yaml

from conf import settings as sets
# from SHRL.app import operatedb as db


class OperateCfg(object):
    '''操作GitLab'''
    def __init__(self,env):
        self.gl = gitlab.Gitlab(sets.GitLab[env]['url'], sets.GitLab[env]['git_token'], timeout=10)
        self.commit_url = sets.GitLab[env]['url'] + '/' + sets.GitLab[env]['repository_name'] + '/commit/'
        # self.gl =gitlab.Gitlab.from_config('Gitlab',['../conf/JiraJks.ini'])
        self.gl.auth()
        self.env = env

    def Content(self,project_name,file_path):
        '''获取指定项目指向配置文件'''
        project = self.gl.projects.get(project_name)
        # 获得文件
        f = project.files.get(file_path=file_path, ref='master')
        # 第一次decode获得bytes格式的内容
        content = f.decode()
        # 第二次decode获得str
        content = content.decode()
        # dict_content = yaml.load(content,Loader=yaml.FullLoader)
        # print(type(yaml.load(content,Loader=yaml.FullLoader)))
        return  content
        # 存到本地
        # with open('paramRef.cp36-win_amd64.pyd', 'wb') as code:
        #     code.write(content)

    def Export(self,project_name):
        '''导出项目'''
        project = self.gl.projects.get(project_name)
        export = project.exports.create({})
        # Wait for the 'finished' status
        export.refresh()
        while export.export_status != 'finished':
            time.sleep(1)
            export.refresh()
        # Download the result
        with open('export.tgz', 'wb') as f:
            export.download(streamed=True, action=f.write)


    def Analyse(self,registry_name,application_config_dir,applicaiton_config_type,commit_content,commit_message):
        #设定有序字典
        multijobs_dict = collections.OrderedDict()
        # 配置文件名
        if self.env == 'Staging':
            self.application_config_name = 'application' + '-staging.' + applicaiton_config_type
        elif self.env == 'Prod':
            self.application_config_name = 'application' + '-prod.' + applicaiton_config_type
        else:
            self.application_config_name = ''
        # 应用配置完整路径 ams-server/application-prod.properties
        application_config_path = application_config_dir + '/' + self.application_config_name
        # 源配置文件信息，即要修改的源配置文件
        source_content = self.Content(registry_name, application_config_path)

        if applicaiton_config_type == 'yaml':
            # 将源配置内容转换字典
            content = yaml.load(source_content,Loader=yaml.FullLoader)
            # print(json.dumps(content,indent=4))

        if applicaiton_config_type == 'properties':
            # 转为列表
            source_content_list = source_content.split('\n')
            # 新增或修改配置
            new_list = []
            for line in commit_content.split('\n'):
                if line != '':
                    new_list.append(line)

            # 判断提交信息是否匹配规则
            for line in new_list:
                try:
                    if re.search(r'[a-zA-Z0-9]+', str(line.split('=')[1])) is None:
                        return False, '配置格式不对'
                except Exception as e:
                    sets.logger.error(str(e))
                    return False, '配置格式不对'
            # 将需增加或修改的配置追加到配置文件中
            compare_list = (source_content_list + new_list)
            # 将配置列表转为有序字典，对于本次更新，如已有配置中没有则新增，如已有配置则替换为本次参数
            for line in compare_list:
                try:
                    multijobs_dict[line.split('=')[0]] = line.split('=')[1]
                except Exception as e:
                    multijobs_dict[line] = ''
                    sets.logger.error(e)
        # 将字典转为字符
        update_content = ''
        for k, v in multijobs_dict.items():
                # 如值为空，则该行为注释行
                if v != '':
                    update_content = update_content + k + '=' + v + '\n'
                else:
                    update_content = update_content + k + v + '\n'
        try:
            Cfg_Update_Result = self.Commit(registry_name, commit_message, application_config_path, update_content)
            return True, '[变更成功]({0})'.format(Cfg_Update_Result)
        except Exception as e:
            sets.logger.error(e)
            return False, '变更失败'

    def Commit(self,registry_name,commit_message,application_config_path,update_content):
        '''提交更新'''
        # commit(celebi/cfg-center,ams-server,properties,'redis_timeout=300','增加redis超时时间')
        data = {
            'branch': 'master',
            'commit_message': commit_message,
            'author_name':'shrl_robot',
            'author_email':'shrl_robot@ppmoney.com',
            'actions': [
                {
                    'action': 'update',
                    'file_path': application_config_path,
                    'content': str(update_content),
                    'encoding':'text'
                }
            ]
        }
        project = self.gl.projects.get(registry_name)
        commit_result = project.commits.create(data)
        commit_result = str(commit_result).split(' => ')[1]
        commit_result = eval(commit_result)
        Cfg_Update_Result = self.commit_url + commit_result['id']
        return Cfg_Update_Result

# return (Cfg_Update_Status, Cfg_Update_Result)
# OperateCfg('Staging').Analyse('celebi/cfg-center','shrl','yaml','redis.timeout=6000','I Just Make A Test!!!')
# status,result = OperateCfg('Staging').Analyse('celebi/cfg-center','ams-server','properties','{"server":[{"port":9085}]','test')
# status,result = OperateCfg('Staging').Analyse('celebi/cfg-center','arceus-server-chjtest','properties','new.property=newValue','test')
# print(status,result)
# OperateCfg('Prod')
# OperateCfg('Staging').Content('celebi/cfg-center','shrl/application-staging.yaml')