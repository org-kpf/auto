import re
import time
from Testbed import testbed
import random
import paramiko
class snapshot():
    def __init__(self,id,name,snap_name,size,allocated_size,status,volume_id,volume_name,cluster):
        self.id = id
        self.name = name
        self.snap_name = snap_name
        #size和allocated_size的单位都是B
        self.size = size
        self.allocated_size = allocated_size
        self.status = status
        self.volume_id = volume_id
        self.volume_name = volume_name
        self.cluster = cluster
    def get_available_node(self):
        class no_available_ip(Exception):
            pass
        # normal_node = paramiko.SSHClient()
        # normal_node.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        # print('收到的pool_cluster是',self.cluster)
        if self.cluster == 'cluster1':
            ip_list = testbed.cluster1[1]
            test_user = testbed.cluster1[4]
            test_password = testbed.cluster1[5]
            test_admin_user = testbed.cluster1[6]
            test_admin_password = testbed.cluster1[7]
        elif self.cluster == 'cluster2':
            ip_list = testbed.cluster2[1]
            test_user = testbed.cluster2[4]
            test_password = testbed.cluster2[5]
            test_admin_user = testbed.cluster2[6]
            test_admin_password = testbed.cluster2[7]
        else:
            raise no_available_ip('输入集群名称错误')
        normal_node = paramiko.SSHClient()
        normal_node.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        #print('pool_cluster是', self.cluster)
        bad_ip_list = []
        for a in ip_list:
            try:
                normal_node.connect(hostname=a, username=test_user, password=test_password)
            except:
                bad_ip_list.append(a)
        for b in bad_ip_list:
            ip_list.remove(b)
        time.sleep(1)
        class empty_ip_list(Exception):
            pass
        if ip_list == []:
            raise empty_ip_list('集群没有可登录的节点')
        else:
            return [random.choice(ip_list),test_user,test_password,test_admin_user,test_admin_password]
    def create_snapshot(self,name,block_volume,description):
        '''
        由卷对象调用，传入名称，卷ID，描述，返回创建命令的后半段
        :param name: 新建快照的名称
        :param block_volume: 原卷的ID
        :param description: 新建快照的描述
        :return: 字符串
        '''
        if description != '':
            return 'block-snapshot create --block-volume=%d --description=%s %s' %(block_volume,description,name)
        if description == '':
            return 'block-snapshot create --block-volume=%d %s' %(block_volume,name)
    def delete(self,check_times=5,check_interval=5):
        '''
        只有snapshot对象可以调用delete删除自己
        :param check_times: 循环检查快照是否删除成功，循环检查次数，默认5次
        :param check_interval: 循环检查快照是否删除成功，循环检查间隔，默认5秒
        :return: 如果预期删除失败，则返回错误的回显；如果预期删除成功，则没有返回
        '''
        class delete_snapshot_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'block-snapshot delete %d' % self.id
        cmd = cmd1 + cmd2
        print('下发删除pool的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return result_err + result_out
        # 判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s block-snapshot list -q "id:%d"''' \
                  % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
                # 移除对象self
                print('第%d次检查，删除%s号快照成功' % (i+1,self.id))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，删除%s号快照失败，快照状态是%s' % ((i+1), self.id,result_out))
                i += 1
            elif i == check_times:
                raise delete_snapshot_failed('循环检查结束，删除%d号快照失败' % self.id)
    def set(self,check_times=0,check_interval=0,**kwargs):
        '''

        :param name: 更改后的快照名称
        :param description: 更改后的快照描述
        :param check_times: 循环检查次数
        :param check_interval: 循环检查时间间隔
        :return: 更改后的快照对象
        '''
        class set_snapshot_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s block-snapshot set' % (temporary_node[3], temporary_node[4])
        cmd2 = ''
        cmd3 = ' %d' % self.id
        for i in kwargs:
            cmd2 = cmd2 + ' --' + i + '=%s' % kwargs.get(i)
        cmd = cmd1 + cmd2 + cmd3
        print('下发修改%d号快照的命令\n%s' %(self.id,cmd))
        stdin,stdout,stderr = ssh.exec_command(cmd)
        out = stdout.read().decode()[:-1]
        err = stderr.read().decode()[:-1]
        print(err + out)
        if err == '':
            pass
        elif out == '' or err != '' or 'Incorrect Usage' in out:
            return (err + out)
        for j in kwargs:
            for i in range(0, check_times):
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-snapshot list -q "id:%d"''' % (j, temporary_node[3], temporary_node[4], self.id))
                result = stdout.read().decode()[:-1]
                if result == kwargs.get(j):
                    print('第%d次检查修改快照结果，快照的%s为%s,传入值为%s，相同' %(i,j,result,kwargs.get(j)))
                    self.__dict__[j] = kwargs.get(j)
                    break
                if result != kwargs.get(j):
                    print('第%d次检查修改快照结果，快照的%s为%s,传入值为%s，不同' %(i,j,result,kwargs.get(j)))
                    i += 1
                    time.sleep(check_interval)
                if i == check_times:
                    raise set_snapshot_failed('循环检查结束，修改%d号快照后的%s为%s,而传入为%s不一致' %(self.id,j,result,kwargs.get(j)))
