# coding=utf-8
import time
import random
# from Testbed import testbed
import paramiko
import re
class client_group():
    def __init__(self,id,name,type,description,client_num,access_path_num,block_volume_num,status,codes):
        self.id = id
        self.name = name
        self.type = type
        self.description = description
        self.client_num = client_num
        self.access_path_num = access_path_num
        self.block_volume_num = block_volume_num
        self.status = status
        self.codes = codes
    @staticmethod
    def create_client_group(type, description, codes, name):
        #TYPE,客户端组用的协议，取值范围：（iSCSI|FC），二选一，注意iSCSI第一个小写，例子：iSCSI
        #DESCRIPTION,，描述，取值范围不限，例子：laji
        #CODES,如果是iSCSI，则是客户端的业务IP或者IQN，如果是FC，则填WWN
        #遗留问题，虚拟机环境无法创建FC类型的客户端组，所以TYPE如果是FC，我还不知道CODES怎么填
        class create_client_group_failed(Exception):
            pass
        if type not in ['iSCSI', 'FC']:
            print('创建客户端组命令中type参数错误，只能是iSCSI或者FC，注意大小写')
            raise create_client_group_failed('输入的客户端类型不是iSCSI,也不是FC')
        if description != None:
            cmd = 'client-group create --type=%s --description=%s --codes="%s" %s' % (type, description, codes, name)
        if description == None:
            cmd = 'client-group create --type=%s --codes=%s %s' % (type, codes, name)
        return cmd
    def delete(self, check_times=1, check_interval=1):
        '''
        只能由客户端组对象删除自己
        :return:
        '''
        class delete_clientgroup_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'client-group delete %d' % self.id
        cmd = cmd1 + cmd2
        print('下发删除客户端组的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return result_err + result_out
        #判断删除结果
        for i in range(0, check_times):
            cmd = 'xms-cli --user %s --password %s client-group show %d' % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
               #移除对象self
                print('第%d次检查，删除客户端组成功' % (i+1))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，删除客户端组失败，查询结果是%s' % ((i+1), result_out))
                i += 1
            elif i == check_times:
                raise delete_clientgroup_failed('循环检查结束，删除%d号客户端组失败' % self.id)
    def set(self, check_times=0, check_interval=0, **kwargs):
        '''

        :param check_times:
        :param check_interval:
        :param kwargs:可变参数，只能取name，description，codes
        name，设置客户端组的名称
        description，设置客户端组的描述
        codes，设置客户端组的IP或者IQN或者WWN
        :return:命令下发失败，返回错误的回显；循环检查修改成功，然后修改对应的值
        '''
        class set_clientgroup_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s client-group set' % (temporary_node[3], temporary_node[4])
        cmd2 = ''
        cmd3 = ' %d' % self.id
        for i in kwargs:
            cmd2 = cmd2 + ' --' + i + '=%s' % kwargs.get(i)
        cmd = cmd1 + cmd2 + cmd3
        print('下发修改%d号客户端组的命令\n%s' % (self.id, cmd))
        stdin, stdout, stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()[:-1]
        err = stderr.read().decode()[:-1]
        print(err + out)
        if err == '':
            pass
        elif out == '' or err != '' or 'Incorrect Usage' in out:
            return (err + out)
        for j in kwargs:
            for i in range(0, check_times):
                if j in ['name', 'description']:
                    stdin, stdout, stderr = ssh.exec_command("xms-cli --user %s --password %s client-group show %d | grep %s | awk '{print $4}'"% (temporary_node[3], temporary_node[4], self.id,j))
                    result = stdout.read().decode()[:-1]
                    if result == kwargs.get(j):
                        print('第%d次检查修改客户端组结果，客户端组的%s为%s,传入值为%s，相同' % (i, j, result, kwargs.get(j)))
                        self.__dict__[j] = kwargs.get(j)
                        break
                    if result != kwargs.get(j):
                        print('第%d次检查修改客户端组结果，客户端组的%s为%s,传入值为%s，不同' % (i, j, result, kwargs.get(j)))
                        i += 1
                        time.sleep(check_interval)
                    if i == check_times:
                        raise set_clientgroup_failed('循环检查结束，修改%d号客户端组后的%s为%s,而传入为%s不一致' % (self.id, j, result, kwargs.get(j)))
                if j in ['codes']:
                    stdin, stdout, stderr = ssh.exec_command("xms-cli -f '{{range .}}{{println .clients}}{{end}}' --user %s --password %s client-group list | grep id:%d" %(temporary_node[3], temporary_node[4],self.id))
                    out = stdout.read().decode()[:-1]
                    result = re.findall('(?<= code:)\S*',out)[0]
                    if result == kwargs.get(j):
                        self.__dict__[j] = kwargs.get(j)
                    if result != kwargs.get(j):
                        print('第%d次检查修改快照结果，快照的%s为%s,传入值为%s，不同' % (i, j, result, kwargs.get(j)))
                        i += 1
                        time.sleep(check_interval)
                    if i == check_times:
                        raise set_clientgroup_failed('循环检查结束，修改%d号快照后的%s为%s,而传入为%s不一致' % (self.id, j, result, kwargs.get(j)))