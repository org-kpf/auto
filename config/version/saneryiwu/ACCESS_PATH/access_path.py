import paramiko
import time
import random
from Testbed import testbed
class access_path():
    def __init__(self, id, name, type, description, protection_domain_id, volume_num,client_group_num,chap, tname, tsecret, status, action_status, create, cluster):
        self.id = id
        self.name = name
        self.type = type
        self.description = description
        self.protection_domain_id = protection_domain_id
        self.volume_num = volume_num
        self.client_group_num = client_group_num
        self.chap = chap
        self.tname = tname
        self.tsecret = tsecret
        self.status = status
        self.action_status = action_status
        self.create = create
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
    def create_access_path(self,type,name,tname,tsecret,chap,description):
        #name，长度不超过128个字符
        #type，取值范围（iSCSI|FC|Local）三选一
        #chap，取值范围（true|false）二选一
        #tname，长度1-223个字符，内容只能包含大小写字母，数字，下划线，点号，冒号，连接符
        #tsecret，长度12-16个字符，内容只能包含大小写字母，数字，下划线，点号，冒号，连接符
        if chap == 'false' and description == '':
            cmd = 'access-path create --type %s %s' % (type,name)
        if chap == 'false' and description != '':
            cmd = 'access-path create --type %s --description %s %s' %(type,description,name)
        if chap == 'true' and description != '':
            cmd = 'access-path create --type %s --description %s --chap=%s --tname=%s --tsecret=%s %s' %(type,description,chap,tname,tsecret,name)
        if chap == 'true' and description == '':
            cmd = 'access-path create --type %s --chap=%s --tname=%s --tsecret=%s %s' % (type, chap, tname, tsecret, name)
        return cmd
    def delete(self, check_times=10, check_interval=5):
        '''
        只能由网关服务器对象调用删除的方法
        :return:
        '''

        class delete_accesspath_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'access-path delete %d' % self.id
        cmd = cmd1 + cmd2
        print('下发删除访问路径的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            print(result_err + result_out)
            raise delete_accesspath_failed('删除访问路径命令返回错误的回显')
        # 判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s access-path list -q "id.raw:%d"''' \
                  % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
                # 移除对象self
                print('第%d次检查，删除访问路径成功' % (i + 1))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，删除访问路径失败，移除后，网关服务器状态是%s' % ((i + 1), result_out))
                i += 1
            elif i == check_times:
                raise delete_accesspath_failed('循环检查结束，删除%d号访问路径失败' % self.id)
        ssh.close()
    def set(self,check_times=0,check_interval=0,**kwargs):
        '''
        访问路径对象，修改自己的各项属性
        :param name: 新名称
        :param description:新描述
        :param chap: 修改开关，取值范围：open/close 二选一
        :param tname:目标端名称长度1-223个字符，内容只能包含大小写字母，数字，下划线，点号，冒号，连接符
        :param tsecret:目标端密钥长度12-16个字符，内容只能包含大小写字母，数字，下划线，点号，冒号，连接符
        :return:
        '''
        class set_accesspath_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s access-path set' % (temporary_node[3], temporary_node[4])
        cmd2 = ''
        cmd3 = ' %d' % self.id
        for i in kwargs:
            cmd2 = cmd2 + ' --' + i + '=%s' % kwargs.get(i)
        cmd = cmd1 + cmd2 + cmd3
        print('下发修改%d号访问路径的命令\n%s' % (self.id, cmd))
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
                if j in ['name','description','tname','tsecret']:
                    stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s access-path list -q "id:%d"''' % (j, temporary_node[3], temporary_node[4], self.id))
                    result = stdout.read().decode()[:-1]
                    if result == kwargs.get(j):
                        print('第%d次检查修改访问路径结果，访问路径的%s为%s,传入值为%s，相同' % (i, j, result, kwargs.get(j)))
                        self.__dict__[j] = kwargs.get(j)
                        break
                    if result != kwargs.get(j):
                        print('第%d次检查修改访问路径结果，访问路径的%s为%s,传入值为%s，不同' % (i, j, result, kwargs.get(j)))
                        i += 1
                        time.sleep(check_interval)
                    if i == check_times:
                        raise set_accesspath_failed(
                            '循环检查结束，修改%d号访问路径后的%s为%s,而传入为%s不一致' % (self.id, j, result, kwargs.get(j)))
                if j in ['chap']:
                    stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s access-path list -q "id:%d"''' % (j, temporary_node[3], temporary_node[4], self.id))
                    result = stdout.read().decode()[:-1]
                    #修改CHAP时，chap开关只接受open/close，API查看的chap开关只能是true/false，提改进
                    if (result == 'true' and kwargs.get(j) == 'open') or (result == 'false' and kwargs.get(j) == 'close'):
                        print('第%d次检查修改访问路径结果，访问路径的%s为%s,传入值为%s，相同' % (i, j, result, kwargs.get(j)))
                        self.__dict__[j] = result
                        break
                    if ( result == 'true' and kwargs.get(j) == 'close' ) or ( result == 'false' and kwargs.get(j) == 'open' ):
                        print('第%d次检查修改访问路径结果，访问路径的%s为%s,传入值为%s，不同' % (i, j, result, kwargs.get(j)))
                        i += 1
                        time.sleep(check_interval)
                    if i == check_times:
                        raise set_accesspath_failed(
                            '循环检查结束，修改%d号访问路径后的%s为%s,而传入为%s不一致' % (self.id, j, result, kwargs.get(j)))

