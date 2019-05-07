import random
from Testbed import testbed
import paramiko
import time
class mapping_group():
    def __init__(self,id,access_path_id,access_path_name,client_group_id,client_group_name,status,create_time,cluster):
        self.id = id
        self.access_path_id = access_path_id
        self.access_path_name = access_path_name
        self.client_group_id = client_group_id
        self.client_group_name = client_group_name
        self.status = status
        self.create_time = create_time
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
    def create_mapping_group(self,block_volumes_ids,access_path,client_group):
        if client_group != '':
            cmd = 'mapping-group create --access-path=%d --block-volumes=%s --client-group=%d' %(access_path,block_volumes_ids,client_group)
        if client_group == '':
            cmd = 'mapping-group create --access-path=%d --block-volumes=%s' %(access_path,block_volumes_ids)
        return cmd
    def remove(self,block_volumes_ids):
        '''

        :param block_volumes_ids: 要移除的卷的id列表，例子：[1,2,3]
        :return: 由NODE对象调用这个方法，这个方法给NODE对象返回拼接的命令片段
        '''

        class remove_mapping_volume_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        for i in range(0,len(block_volumes_ids)):
            for j in block_volumes_ids:
                block_volumes_ids.remove(j)
                block_volumes_ids.append(str(j))
        block_volumes_ids = ','.join(block_volumes_ids)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s '%(temporary_node[3],temporary_node[4])
        cmd2 = 'mapping-group remove block-volume %d %s' %(self.id,block_volumes_ids)
        cmd = cmd1 + cmd2
        print('下发映射组移除卷的命令\n',cmd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        print(result_err + result_out)
        if result_out == '' or result_err != '':
            raise remove_mapping_volume_failed('映射组移除卷命令执行失败')
        else:
            return result_out
    def delete(self, check_times=5, check_interval=5):
        '''

        :param check_times:
        :param check_interval:
        :return:
        '''
        class delete_mappinggroup_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' %(temporary_node[3],temporary_node[4])
        cmd2 = 'mapping-group delete %d' %self.id
        cmd = cmd1 + cmd2
        print('下发删除映射组的命令\n',cmd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return result_err + result_out
        #判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s mapping-group list -q "id:%d"''' \
                  % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
               #移除对象self
                print('第%d次检查，删除映射组成功' %(i+1))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，删除映射组失败，移除后，映射组状态是%s' %((i+1),result_out))
                i += 1
            elif i == check_times:
                raise delete_mappinggroup_failed('循环检查结束，删除%d号映射组失败' %self.id)
    def add(self,block_volumes_ids):
        '''

        :param id: mapping_group的id，
        :param block_volume_ids: 卷的id列表，例子：1,2,3
        :return: 由NODE对象调用这个方法，这个方法给NODE对象返回拼接的命令片段
        '''
        class add_mapping_volume_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s '%(temporary_node[3],temporary_node[4])
        cmd2 = 'mapping-group add block-volume %d %s' %(self.id,block_volumes_ids)
        cmd = cmd1 + cmd2
        print('下发映射组添加卷的命令\n',cmd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        print(result_err + result_out)
        if result_out == '' or result_err != '':
            raise add_mapping_volume_failed('映射组添加卷命令执行失败')
        else:
            return result_out
    def set(self,block_volumes_ids):
        '''

        :param block_volume_ids: 卷ID列表，设置映射组里的卷，设置之后映射组里只有列表中的卷，例子：[1,2,3]
        :return: 下发成功，无返回；下发失败，返回失败的回显
        '''
        class set_mappinggroup_failed(Exception):
            pass

        temporary_node = self.get_available_node()
        for i in range(0, len(block_volumes_ids)):
            for j in block_volumes_ids:
                block_volumes_ids.remove(j)
                block_volumes_ids.append(str(j))
        block_volumes_ids = ','.join(block_volumes_ids)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'mapping-group set block-volume --block-volumes=%s %d' % (block_volumes_ids, self.id)
        cmd = cmd1 + cmd2
        print('下发修改映射组的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        print(result_err + result_out)
        if result_out == '' or result_err != '' or 'Incorr' in result_out:
            raise set_mappinggroup_failed('映射组移除卷命令执行失败')
        else:
            return result_out + result_err
