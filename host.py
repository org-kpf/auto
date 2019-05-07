# coding=utf-8
import paramiko
import re
import time
# from Testbed import testbed
import random
class host():
    def __init__(self,id,name,type,roles,public_ips,private_ip,admin_ip,gateway_ip,description,protection_domain_id,status,up):
        self.id = id
        self.name = name
        self.type = type
        self.roles = roles
        self.public_ips = public_ips
        self.private_ip = private_ip
        self.admin_ip = admin_ip
        self.gateway_ips = gateway_ip
        self.description = description
        self.protection_domain_id = protection_domain_id
        self.status = status
        self.up = up

    @staticmethod
    def add_host(public_ip, private_ip, gateway_ip, admin_ip, roles, type, description):
        '''
        :param public_ip:必选，公共IP，从测试床中读取，例子：10.252.2.81
        :param private_ip:必选，集群内部用于互联的IP，从测试床中读取，例子：10.252.1.81
        :param gateway_ip:必选，集群网关IP，可以和公共IP相同，从测试床中读取，例子：10.252.2.81
        :param admin_ip:必选，集群管理IP，从测试床中读取，例子：10.252.3.81
        :param roles: 添加服务器的角色，取值范围（admin|monitor|metadata|block_storage_gateway|s3_gateway|nfs_gateway, seperated by comma）七选多，
        命令默认，nfs_gateway,s3_gateway，实际默认：nfs_gateway,s3_gateway,block_storage_gateway,file_storage_gateway
        :param type: 添加服务器的类型，取值范围（storage_server|storage_client），二选一，默认：storage_server
        :param description:描述，任意字符串，例子：abc，默认为空
        :return:
        '''
        if description == '':
            cmd = 'host create --type %s --roles %s --public-ip %s --private-ip %s --gateway-ips %s %s' \
                  %(type, roles, public_ip, private_ip, gateway_ip, admin_ip)
        else:
            cmd = 'host create --type %s --roles %s --description %s --public-ip %s --private-ip %s --gateway-ips %s --description %s %s' \
                  %(type, roles, description, public_ip, private_ip, gateway_ip,description, admin_ip)
        return cmd

    def set(self,check_times=0,check_interval=0,**kwargs):
        '''
        CLI有个限制，一次只能修改roles或者只能修改description
        :param check_times: 循环检查修改服务器是否成功，循环检查次数,一般需要200秒才能修正完成
        :param check_interval: 循环检查修改服务器是否成功，检查时间间隔，单位：秒
        :param kwargs: 只能选择roles或者description
        roles，服务器新角色，EBS的取值范围：admin,monitor,block_storage_gateway 三选多；EDP的取值范围：
        admin,monitor,block_storage_gateway,s3_gateway,nfs_gateway,file_storage_gateway 六选多
        :return:如果下发失败，返回错误的回显；如果下发成功，并且有循环检查，修改host对象的特性为新值
        '''
        class set_host_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s host set' % (temporary_node[3], temporary_node[4])
        cmd2 = ''
        cmd3 = ' %d' % self.id
        for i in kwargs:
            cmd2 = cmd2 + ' --' + i + '=%s' % kwargs.get(i)
        cmd = cmd1 + cmd2 + cmd3
        print('下发修改%d号服务器的命令\n%s' % (self.id, cmd))
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
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s host list -q "id:%d"''' % (j, temporary_node[3], temporary_node[4], self.id))
                result = stdout.read().decode()[:-1]
                if result == kwargs.get(j):
                    print('第%d次检查修改服务器结果，服务器的%s为%s,传入值为%s，相同' % (i, j, result, kwargs.get(j)))
                    self.__dict__[j] = kwargs.get(j)
                    break
                if result != kwargs.get(j):
                    print('第%d次检查修改服务器结果，服务器的%s为%s,传入值为%s，不同' % (i, j, result, kwargs.get(j)))
                    i += 1
                    time.sleep(check_interval)
                if i == check_times:
                    raise set_host_failed('循环检查结束，修改%d号服务器后的%s为%s,而传入为%s不一致' % (self.id, j, result, kwargs.get(j)))
    def show_host(self):
        '''
        host对象查看自己的属性，并更新自己的特性参数
        :return: 更新后的host对象
        '''
        class show_host_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        ssh.connect(hostname=temporary_node[0],username=temporary_node[1],password=temporary_node[2])
        if self.id != 1:
            stdin,stdout,stderr = ssh.exec_command('xms-cli --user %s --password %s host show %d' %(temporary_node[3],temporary_node[4],self.id))

        #去掉返回结果开头两行和最后一行
        result = stdout.read().decode()
        if result =='':
            show_host_failed('查询服务器失败')
        print(result)
        #用返回结果中的字段，更新对象的特性
        self.id = int(re.findall('(?<=\| id                   \| )\w*', result)[0])
        self.name = re.findall('(?<=\| name                 \| )\S*',result)[0]
        self.type = re.findall('(?<=\| type                 \| )\S*',result)[0]
        self.roles = re.findall('(?<=\| roles                \| )\S*',result)[0]
        self.public_ips = re.findall('(?<=\| public_ips           \| )\S*',result)[0]
        self.private_ip = re.findall('(?<=\| private_ip           \| )\S*',result)[0]
        self.admin_ip = re.findall('(?<=\| admin_ip             \| )\S*', result)[0]
        self.gateway_ips = re.findall('(?<=\| gateway_ips          \| )\S*', result)[0]
        self.description = re.findall('(?<=\| description          \| )\S*', result)[0]
        self.protection_domain_id = int(re.findall('(?<=\| protection_domain.id \| )\w*',result)[0])
        self.status = re.findall('(?<=\| status               \| )\w*',result)[0]
        self.up = re.findall('(?<=\| up                   \| )\w*', result)[0]
    def delete(self,check_times=10,check_interval=5):
        '''

        :param check_times: 循环检查删除成功，检查次数
        :param check_interval: 循环检查删除成功，检查时间间隔
        :return:
        '''
        class delete_host_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        stdin,stdout,stderr = ssh.exec_command('xms-cli --user %s --password %s host delete %d' %(temporary_node[3],temporary_node[4],self.id))
        out = stdout.read().decode()[:-1]
        err = stderr.read().decode()[:-1]
        if err != '':
            print('删除%d号服务器失败\n%s' %(self.id,err))
            return err+out
        else:
            for i in range(0,check_times):
                stdin,stdout,stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s host list -q "id:%d"''' %(temporary_node[3],temporary_node[4],self.id))
                result_out = stdout.read().decode()[:-1]
                result_err = stderr.read().decode()[:-1]
                if result_out == '' and result_err == '':
                    # 移除对象self
                    print('第%d次检查，删除host成功' % (i + 1))
                    del self
                    break
                if result_out != '':
                    time.sleep(check_interval)
                    print('第%d次检查，删除host失败，host状态是%s' % ((i + 1), result_out))
                    i += 1
                elif i == check_times:
                    raise delete_host_failed('循环检查结束，删除%d号host失败' % self.id)

if __name__ == "__main__":
    test = host('1','node1',type=1,roles=1,public_ips=1,private_ip=1,admin_ip=1,gateway_ip=1,description=None,protection_domain_id=1,status=1,up=1)
    out = test.add_host(type='storage_server', roles='block_storage_gateway', public_ip='10.252.2.80',
                             private_ip='10.252.1.80',
                             gateway_ip='10.252.2.80', admin_ip='10.252.3.80')
    print(out)


