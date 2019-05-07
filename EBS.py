# coding=utf-8
import paramiko
#from config.XebsException import ceph_status_error
import sys
sys.path.append('..')
reload(sys)
sys.setdefaultencoding("utf-8")
import socket
from host import host as host
from pool import pool as pool
from client_group import client_group as client_group
from access_path import access_path as access_path
from target import target as target
from mapping_group import mapping_group as mapping_group
from osd import osd
from volume import volume
from partition import partition
from nodeFault import nodeFault as nodeFault

import time
import re
import os

class EBS(object):

    # def __init__(self, ip, port, user, password, admin_user='admin', admin_password='admin', cluster='cluster2'):
    # def __init__(self, ip, user, password, port=22, admin_user='admin', admin_password='admin', cluster='cluster1'):
    #     self.ip = ip
    #     self.port = port
    #     self.user = user
    #     self.password = password
    #     self.admin_user = admin_user
    #     self.admin_password = admin_password
    #     self.cluster = cluster

    def ebs_connect(self, ip, user, password, admin_user, admin_password, port=22):
        self.ip = ip
        self.user = user
        self.password= password
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.port = port
        class connect_cluster_failed(Exception):
            pass
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result = self.cmd('xms-cli --user %s --password %s host list' % (self.admin_user, self.admin_password))

        return result
        #id = int(re.findall('(?<=\| id                   \| )\w*', result)[0])
        #name = re.findall('(?<=\| name                 \| )\S*', result)[0]
        #type = re.findall('(?<=\| type                 \| )\S*', result)[0]
        #roles = re.findall('(?<=\| roles                \| )\S*', result)[0]
        #public_ips = re.findall('(?<=\| public_ips           \| )\S*', result)[0]
        #private_ip = re.findall('(?<=\| private_ip           \| )\S*', result)[0]
        #admin_ip = re.findall('(?<=\| admin_ip             \| )\S*', result)[0]
        #gateway_ips = re.findall('(?<=\| gateway_ips          \| )\S*', result)[0]
        #description = re.findall('(?<=\| description          \| )\S*', result)[0]
        #protection_domain_id = int(re.findall('(?<=\| protection_domain.id \| )\w*', result)[0])
        #status = re.findall('(?<=\| status               \| )\w*', result)[0]
        #up = re.findall('(?<=\| up                   \| )\w*', result)[0]
        #return host(id, name, type, roles, public_ips, private_ip, admin_ip, gateway_ips, description, protection_domain_id, status, up)

    def vip(self,ip,user,password,admin_user,admin_password,port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.port = port
        class vip_get_fail(Exception):
            pass
        self.transport = paramiko.Transport(self.ip,self.port)
        self.transport.connect(username=self.user,password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result = self.cmd("xms-cli --user %s  --password %s fs-gateway list" %(self.admin_user,self.admin_password))
        #print result
        if "VIP" in result:
            return result
        else:
            raise  vip_get_fail("%s"  % result)


    def Ping(self,ips):
         ipsl = ips.split(" ")
         iplist = list()
         for ip in ipsl:
             backinfo = os.system("ping %s" % ip)
             #print "ping 通返回:",backinfo
             if backinfo!=0:
                 continue
             else:
                 iplist.append(ip)
                 break
         return ''.join(iplist)

    #定时
    def timing(self,num):
        class timing(Exception):
            pass
        N = 2880
        if num == N:
            raise timing("loop %s exit " %(num))
        else:
            return num

    def cmd(self,cmd):
        class cmd_execute_faild(Exception):
            pass
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd)
        except socket.error as e:
            ssh._transport = self.transport
            stdin, stdout, stderr = ssh.exec_command(cmd)
        resultout = stdout.read().decode()[:-1]
        resulterr = stderr.read().decode()[:-1]
        #用不存在的osd和缺少名称的命令创建pool，返回结果中的out和err都不为空，都返回
        if resulterr == '' and resultout != '':
            return resultout
        #如果创卷没有设置QOS,用API取一般属性和qos属性，一般属性作为out返回，qos属性作为err返回，应该只返回out或者err？
        elif resulterr != '' and resultout != '':
            return resulterr
        elif resulterr == '' and resultout == '':
            return ''
        elif resulterr != '' and resultout == '':
            return resulterr
        ssh.close()

    def put(self, server_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(local_path, server_path)

    def get(self, server_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.get(server_path, local_path)

    #集群状态
    def check_ceph_status(self,ip,user,password,port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.port = port
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result_status = self.cmd("ceph -s| grep health | awk {'print $2'}")
        if result_status == 'HEALTH_OK':
            return "HEALTH_OK"
        else:
            return result_status


    #得到mon leader
    def check_ceph_mon_status(self):
        class ceph_err(Exception):
            pass
        result_status = self.cmd("ceph mon stat |awk -F'},' '{print $2}'|awk -F',' '{print $2}'")
        return result_status

    #bmc 网段转化
    def trans_ip(self,ip,bmcnet):
        self.ip = ip
        self.bmcnet = bmcnet
        list = ip.split(".")
        list[2] = bmcnet
        return ("%s.%s.%s.%s") %(list[0],list[1],list[2],list[3])


    #得到文件网关节点
    def get_file_gateway(self, ip, user, password, admin_user, admin_password, port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.port = port
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result_file_gwip = self.cmd("xms-cli   -f '{{range .}}{{println .roles .admin_ip}}{{end}}'  --user %s --password %s host list| grep 'file_storage_gateway'|awk -F' ' '{print $2}'" % (self.admin_user, self.admin_password))
        list = result_file_gwip.split("\n")
        #print type(list)
        return list

    #得到块网关节点
    def get_block_gateway(self, ip, user, password, admin_user, admin_password, port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.port = port
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result_block_gwip = self.cmd("xms-cli   -f '{{range .}}{{println  .admin_ip}}{{end}}'  --user %s --password %s host list" % (self.admin_user, self.admin_password))
        return result_block_gwip

    #得到管理角色节点
    def get_admin(self, ip, user, password, admin_user, admin_password, port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.port = port
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result_adminip = self.cmd("xms-cli   -f '{{range .}}{{println .roles .admin_ip}}{{end}}'  --user %s --password %s host list|grep 'admin'|awk -F' '  '{print $2}'" % (self.admin_user, self.admin_password))
        return result_adminip

    #得到监控角色节点
    def get_monitor(self,ip,user,password,admin_user,admin_password,port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.port = port
        self.transport = paramiko.Transport(self.ip,self.port)
        self.transport.connect(username=self.user,password=self.password)
        print ('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result_get_monitor = self.cmd("xms-cli   -f '{{range .}}{{println .roles .admin_ip}}{{end}}'  --user %s --password %s host list|grep 'monitor'|awk -F' '  '{print $2}'" % (self.admin_user, self.admin_password))
        return result_get_monitor

    #重启文件网关节点
    def power_filegw(self,bmcip,bmcuser,bmcpassword,sleepTime):
        class power_filegw(Exception):
            pass
        cmdoff = nodeFault.powerdown(bmcip,bmcuser,bmcpassword)
        print cmdoff
        resultoff = self.cmd(cmdoff)
        print "sleep %s" %sleepTime
        time.sleep(int(sleepTime))
        cmdon = nodeFault.poweron(bmcip,bmcuser,bmcpassword)
        print cmdon
        resulton = self.cmd(cmdon)

        if resultoff =="Chassis Power Control: Down/Off" and resulton == "Chassis Power Control: Up/On":
            return resultoff,resulton
        else:
            raise  power_filegw("power fail: %s %s") % (resultoff,resulton)


    #重启块网关节点


    def CreatePool(self, osds, name, type='replicated', size=2, pool_role='data', failure_domain_type='host',
                   data_chunk_num=2, coding_chunk_num=1, check_times=0, check_interval=0):
        '''
        :param osds: 必选，创建存储池用到的osd的列表
        :param type: 必选，（replicated|erasure）二选一，默认：replicated
        :param size:如果type为replicated则必选，取值范围：自然数（1-6），默认：2
        :param pool_role:可选，取值范围（data|index）二选一，默认：data
        :param failure_domain_type:可选，取值范围（host|rack|datacenter）三选一，默认：host
        :param data_chunk_num:可选，EC池必选，取值范围：自然数，默认：2
        :param coding_chunk_num:可选，EC池必选，取值范围：自然数，默认：1
        :param name:必选，取值范围,小于等于128个字符，可以包括大小写字母，数字，点号（.），下划线（_），连接符（-），例子：aa
        :param check_times:默认0，一次也不检查
        :param check_interval:默认0，不检查
        :return:如果预期成功，则返回存储池对象；如果预期失败，则返回报错信息
        如果预期创建成功，需要设置两个循环检查参数，函数返回pool对象
        如果预期创建失败，不带两个循环检查参数，函数返回错误信息
        '''
        class create_pool_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s' %(self.admin_user,self.admin_password)
        #把整型的osds列表转成字符串
        print(cmd1)
        for i in range(0,len(osds)):
            for j in osds:
                osds.remove(j)
                osds.append(str(j))
        osds = ','.join(osds)
        cmd2 = pool.create_pool(osds, type, size, pool_role, failure_domain_type, name, data_chunk_num, coding_chunk_num)
        cmd = cmd1 + ' ' + cmd2
        print('下发创建POOL的命令：', cmd)
        result = self.cmd(cmd)
        if 'error' in result:
            return result
        # 循环检查存储池创建成功
        for i in range(0, check_times):
            # 设置检查时间间隔为check_interval秒
            result_status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                     % (self.admin_user, self.admin_password, name))
            # 用交互式解释器，实验一把，其实result的值是active\n
            if result_status == 'active':
                print('第%d次检查创建POOL状态，时间间隔%s秒，POOL的状态是%s,创建POOL成功' % (i, check_interval, result_status))
                #创建成功，返回一个pool对象,pool_mode一直是空的，所以采用awk的方式取字段，如果pool_mode不为空，那么下面的代码其实是有问题的
                #需要改成切片的正则表达式或者用其它的方式
                print('EBS第145行获取到的ID是')
                id = int(self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                  % (self.admin_user, self.admin_password, name)))
                name = name
                protection_domain_id = self.cmd('''xms-cli -f '{{range .}}{{println .protection_domain.id}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                                % (self.admin_user, self.admin_password, name))
                protection_domain_id = int(protection_domain_id)
                replicate_size = self.cmd('''xms-cli -f '{{range .}}{{println .replicate_size}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                          % (self.admin_user, self.admin_password, name))
                replicate_size = int(replicate_size)
                type = self.cmd('''xms-cli -f '{{range .}}{{println .pool_type}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                     % (self.admin_user, self.admin_password, name))
                failure_domain_type = self.cmd('''xms-cli -f '{{range .}}{{println .failure_domain_type}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                               % (self.admin_user, self.admin_password, name))
                device_type = self.cmd('''xms-cli -f '{{range .}}{{println .device_type}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                       % (self.admin_user, self.admin_password, name))
                status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                  % (self.admin_user, self.admin_password, name))
                action_status = self.cmd('''xms-cli -f '{{range .}}{{println .action_status}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                         % (self.admin_user, self.admin_password, name))
                pool_mode = self.cmd('''xms-cli -f '{{range .}}{{println .pool_mode}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                     % (self.admin_user, self.admin_password, name))
                pool_role = self.cmd('''xms-cli -f '{{range .}}{{println .pool_role}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                     % (self.admin_user, self.admin_password, name))
                return pool(id, name, protection_domain_id, replicate_size, type, failure_domain_type, device_type, status, action_status, pool_mode, pool_role)
            elif result_status != 'active':
                print('第%d次检查创建POOL状态，时间间隔%s秒，POOL的状态是%s,继续' % (i, check_interval,result_status))
                time.sleep(check_interval)
                i += 1
            if i == check_times:
                print('第%d次检查创建POOL状态，创建POOL失败' % check_times)
                raise create_pool_failed('循环检查结束，pool的状态不正常')

    def ShowPool(self, name, check_times=1, check_interval=1):
        '''
        :param name: 要查询的POOL的名称，与创建时的名称相同
        :param check_times: 循环检查POOL的状态为active,循环检查次数，默认：1
        :param check_interval: 循环检查POOL的状态为active，循环检查时间间隔，默认：1
        :return: 如果状态为active，返回POOL对象；如果状态不为active，抛异常
        '''
        class show_pool_failed(Exception):
            pass
        for i in (0, check_times):
            result_status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                     % (self.admin_user, self.admin_password, name))
            if result_status == 'active':
                result = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .protection_domain.id}}{{println .replicate_size}}{{println .pool_type}}{{println .failure_domain_type}}{{println .device_type}}{{println .status}}{{println .action_status}}{{println .pool_mode}}{{println .pool_role}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                  % (self.admin_user, self.admin_password, name))
                result = result.split('\n')
                id = int(result[0])
                name = result[1]
                protection_domain_id = int(result[2])
                replicate_size = int(result[3])
                type = result[4]
                failure_domain_type = result[5]
                device_type = result[6]
                status = result[7]
                action_status = result[8]
                pool_mode = result[9]
                pool_role = result[10]
                return pool(id, name, protection_domain_id, replicate_size, type, failure_domain_type, device_type, status, action_status, pool_mode, pool_role)
            if result_status != 'active':
                time.sleep(check_interval)
                i += 1
            if i == 'check_times':
                raise show_pool_failed('循环检查结束，查询pool状态为%s' % result_status)

    def DeletePool(self, name, force='false', check_times=0, check_interval=0):
        '''

        :param name: 待删除卷的名称
        :param force: 是否强制删除，取值范围true和false二选一，例子：true，默认：false
        :param check_times: 删除后，检查是否删除成功，检查次数
        :param check_interval: 删除后，检查是否删除成功，检查间隔，单位秒
        :return:
        '''
        class delete_pool_failed(Exception):
            pass
        #根据name获取pool的ID
        id = int(self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"''' % (self.admin_user, self.admin_password, name)))
        cmd1 = 'xms-cli --user %s --password %s' % (self.admin_user, self.admin_password)
        # cmd2 = pool.create_pool(osds, type, size, pool_role, failure_domain_type, name, data_chunk_num,coding_chunk_num)
        cmd2 = pool.delete_pool(id, force)
        cmd = cmd1 + ' ' + cmd2
        print(cmd)
        delete_status = self.cmd(cmd)
        if delete_status == '':
            raise delete_pool_failed('删除pool的命令返回为空')
        elif 'deleting' not in delete_status:
            print(delete_status)
            return delete_status
        for i in range(0, check_times):
            result = self.cmd("xms-cli --user %s --password %s pool show %d" % (self.admin_user, self.admin_password, id))
            if 'pool not found: %d' % id in result:
                print('第%d次检查，间隔%d秒，删除存储池成功' % (i, check_interval))
                return None
            if 'pool not found: %d' % id not in result:
                print('第%d次检查，间隔%d秒，删除存储池结果是%s，继续' % (i, check_interval, result))
                time.sleep(check_interval)
                i += 1
            if i == check_times:
                raise delete_pool_failed('第%d次检查，间隔%d秒，删除存储池失败，结果是%s' % (i, check_interval, result))

    def CreateVolume(self, pool_id, size, name, qos_enabled='false', max_total_iops=1000, max_total_bw=4194304000,
                     max_burst_iops=2000, max_burst_bw=8388608000, format=128, performance_priority=0, check_times=0,
                     check_interval=0):
        '''

        :param size: VOLUME的大小，单位：B,例子1：104857600  例子2：20GB
        :param name: volume的名称
        :param format: 指定VOLUME的类型，取值范围（2|128|129），分别对应V2|V3|V4类型的VOLUME，默认128
        :param performance_priority: 性能优先级，取值范围（0|1），分别是（默认|优先），默认是0
        :param qos_enabled: QoS开关，默认：关闭，例子：yes
        :param max_total_iops: 最大IOPS，取值范围，自然数，默认是0，表示不限制IOPS
        :param max_total_bw: 最大带宽，取值范围，自然数，单位B/s
        :param max_burst_iops: 突发IOPS，突发IOPS要大于等于最大IOPS
        :param max_burst_bw: 突发带宽，取值范围，自然数，单位B/s，突发带宽要大于等于最大带宽
        :param check_times:
        :param check_interval:
        :return:
        '''

        class create_volume_failed(Exception):
            pass

        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = volume.create_volume(pool_id, size, name, format, performance_priority, qos_enabled, max_total_iops,
                                    max_total_bw, max_burst_iops, max_burst_bw)
        cmd = cmd1 + cmd2
        result = self.cmd(cmd)

        if 'error' in result:
            print('Create VOLUME %s Failed' %name)
            return result
        else:
            id = int(re.findall('(?<=\| id                   \| )\w*', result)[0])

        for i in range(0, check_times):
            stdout_result_status = self.cmd(
                "xms-cli --user %s --password %s block-volume show %d" % (self.admin_user, self.admin_password, id))

            result = re.findall('(?<=\| status               \| )\w*', stdout_result_status)[0]
            # 用交互式解释器，实验一把，其实result的值是active\n
            if result == 'active':
                print('第%d次检查创建volume状态，volume的状态是%s,创建volume成功' % (i, result))
                # 需要改成切片的正则表达式或者用其它的方式
                # 查看新创建的volume的id
                id = id
                print('id', id)
                size = re.findall('(?<=\| size                 \| )\w* \w*', stdout_result_status)[0]
                size = size.split(' ')
                size[0] = int(size[0])
                if size[1] == 'GiB':
                    size[1] = 1073741824
                if size[1] == 'MiB':
                    size[1] = 1048576
                if size[1] == 'KiB':
                    size[1] = 1024
                size = size[0] * size[1]
                print('size', size)
                pool_id = int(re.findall('(?<=\| pool.id              \| )\w*', stdout_result_status)[0])
                pool_name = re.findall('(?<=\| pool.name            \| )\w*', stdout_result_status)[0]
                snapshot_id = re.findall('(?<=\| snapshot.id          \| )\w*', stdout_result_status)[0]
                snapshot_name = re.findall('(?<=\| snapshot.name        \| )\w*', stdout_result_status)[0]
                status = result
                print('status', status)
                action_status = re.findall('(?<=\| action_status        \| )\w*', stdout_result_status)[0]
                flattened = re.findall('(?<=\| flattened            \| )\w*', stdout_result_status)[0]
                format = re.findall('(?<=\| format               \| )\w*', stdout_result_status)[0]
                description = re.findall('(?<=\| description          \| )\w*', stdout_result_status)[0]
                create = re.findall('(?<=\| create               \| )\w*', stdout_result_status)[0]
                print('create', create)

                try:
                    qos_max_total_iops = int(re.findall('(?<=\| qos.max_total_iops   \| )\w*', stdout_result_status)[0])
                    qos_max_total_bw = int(re.findall('(?<=\| qos.max_total_bw     \| )\w*', stdout_result_status)[0])
                    qos_burst_total_iops = int(re.findall('(?<=\| qos.burst_total_iops \| )\w*', stdout_result_status)[0])
                    qos_burst_total_bw = int(re.findall('(?<=\| qos.burst_total_bw   \| )\w*', stdout_result_status)[0])
                except:
                    qos_max_total_iops = None
                    qos_max_total_bw = None
                    qos_burst_total_iops = None
                    qos_burst_total_bw = None
                sn = self.cmd(
                    '''xms-cli -f '{{range .}}{{println .sn}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"'''
                    % (self.admin_user, self.admin_password, name))
                sn = sn.upper()
                performance_priority = performance_priority
                qos_enabled = qos_enabled
                return volume(id, name, size, pool_id, pool_name, snapshot_id, snapshot_name, status, action_status,
                              flattened, format, qos_max_total_iops, qos_max_total_bw, qos_burst_total_iops,
                              qos_burst_total_bw,description, create, sn, performance_priority, qos_enabled)
            elif result != 'active':
                print('第%d次检查创建volume状态，Volume的状态是%s,继续' % (i, result))
                time.sleep(check_interval)
                i += 1
            if i == check_times:
                create_volume_failed('第%d次检查创建volume状态，循环检查结束，创建volume失败' % check_times)
    def ShowVolume(self,name):
        '''
        这个关键字用于更新volume对象的各个属性
        :param 要查询的卷的名称
        :return: 返回循环检查的结果，并作为新对象返回
        '''
        class show_volume_failed(Exception):
            pass
        out = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .size}}{{println .pool.id}}{{println .pool.name}}{{println .snapshot_id}}{{println .snapshot_name}}{{println .status}}{{println .action_status}}{{println .flattened}}{{println .format}}{{println .description}}{{println .create}}{{println .performance_priority}}{{println .qos_enabled}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"'''% (self.admin_user, self.admin_password, name))
        out = out.split('\n')
        id = int(out[0])
        name = out[1]
        size = int(out[2])
        pool_id = int(out[3])
        pool_name = out[4]
        snapshot_id = out[5]
        snapshot_name = out[6]
        status = out[7]
        action_status = out[8]
        flattened = out[9]
        format = int(out[10])
        description = out[11]
        create = out[12]
        performance_priority = int(out[13])
        qos_enabled = out[14]
        sn = self.cmd('''xms-cli -f '{{range .}}{{println .sn}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"''' % (self.admin_user, self.admin_password, name))
        sn = sn.upper()
        result_out = self.cmd('xms-cli --user %s --password %s block-volume show %d' % (self.admin_user, self.admin_password, id))
        try:
            qos_max_total_iops = int(re.findall('(?<=\| qos.max_total_iops   \| )\w*', result_out)[0])
            qos_max_total_bw = int(re.findall('(?<=\| qos.max_total_bw     \| )\w*', result_out)[0])
            qos_burst_total_iops = int(re.findall('(?<=\| qos.burst_total_iops \| )\w*', result_out)[0])
            qos_burst_total_bw = int(re.findall('(?<=\| qos.burst_total_bw   \| )\w*', result_out)[0])
        except:
            qos_max_total_iops = None
            qos_max_total_bw = None
            qos_burst_total_iops = None
            qos_burst_total_bw = None
        return volume(id, name, size, pool_id, pool_name, snapshot_id, snapshot_name, status, action_status,
                             flattened, format, qos_max_total_iops, qos_max_total_bw, qos_burst_total_iops,
                             qos_burst_total_bw, description, create, sn, performance_priority, qos_enabled)
    def CreateHost(self,public_ip,private_ip,gateway_ip,admin_ip,roles='block_storage_gateway',type='storage_server',description='',check_times=0,check_interval=0):
        '''
        传入服务器类型，服务器角色，private网段ip，public网段ip，private网段ip，admin网段ip，返回添加的服务器对象
        :param roles: 新添加服务器的角色，取值范围：（admin,monitor,s3_gateway,nfs_gateway,block_storage_gateway,file_storage_gateway）选多个，
        默认：block_storage_gateway,s3_gateway,nfs_gateway,file_storage_gateway
        :param public_ip:公共IP，从测试床中读取，例子：10.252.2.81
        :param private_ip:集群内部用于互联的IP，从测试床中读取，例子：10.252.1.81
        :param gateway_ip:集群网关IP，可以和公共IP相同，从测试床中读取，例子：10.252.2.81
        :param admin_ip:集群管理IP，从测试床中读取，例子：10.252.3.81
        :param description:描述，任意字符串，例子：abc，默认为空
        :param type:新添加服务器的类型，取值范围：storage_server和storage_client二选一，默认：storage_server
        :param check_times:循环检查添加成功的次数，默认为0，不检查
        :param check_interval:循环检查添加成功的时间间隔，默认为0，不检查
        :return:不带循环检查时下发成功既返回初始化中的host对象，下发失败失败的回显并弹异常
        带循环检查时，如果检查状态为active，则返回正常的host对象，如果检查状态不为active，抛异常
        '''
        class add_host_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = host.add_host(public_ip, private_ip, gateway_ip, admin_ip, roles, type, description)
        # print(cmd2)
        cmd = cmd1 + cmd2
        # print('下发添加服务器的命令', cmd)
        result = self.cmd(cmd)
        if 'error' in result:
            #raise add_host_failed('下发添加服务器的命令返回错误')
            return result
        # 循环检查添加服务器的状态，直到服务器状态变为active
        for i in range(0, check_times):
            time.sleep(check_interval)
            result = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                              % (self.admin_user, self.admin_password, admin_ip))
            # 用交互式解释器，实验一把，其实result的值是active\n
            if result == 'active':
                print('第%d次检查添加服务器状态，时间间隔%d秒，时间点是\n服务器的状态是%s,添加服务器成功' % (i, check_interval,result))
                id = int(self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip)))
                name = self.cmd('''xms-cli -f '{{range .}}{{println .name}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                type = self.cmd('''xms-cli -f '{{range .}}{{println .type}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                roles = self.cmd('''xms-cli -f '{{range .}}{{println .roles}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                %(self.admin_user, self.admin_password, admin_ip))
                public_ips = self.cmd('''xms-cli -f '{{range .}}{{println .public_ips}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                gateway_ips = self.cmd('''xms-cli -f '{{range .}}{{println .gateway_ips}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                description = self.cmd('''xms-cli -f '{{range .}}{{println .description}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                %(self.admin_user, self.admin_password, admin_ip))
                protection_domain_id = self.cmd('''xms-cli -f '{{range .}}{{println .protection_domain.id}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                up = self.cmd('''xms-cli -f '{{range .}}{{println .up}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                return host(int(id), name, type, roles, public_ips, private_ip, admin_ip, gateway_ips, description, protection_domain_id, 'active', up)
            elif result != 'active':
                print('第%d次检查添加服务器状态，时间间隔%d秒，时间点是\n服务器的状态是%s,继续' % (i, check_interval, result))
                i += 1
            if i == check_times or result == 'installing_error':
                raise add_host_failed('第%d次检查添加服务器状态为%s，时间间隔%d秒，时间点是\n添加服务器失败' % (i, result, check_interval))
    def ShowHost(self, admin_ip, check_times=1, check_interval=1):
        '''
        :param admin_ip: 服务器的管理IP，从测试床读取
        :param check_times: 循环检查服务器状态的次数，服务器为active时，退出检查
        :param check_interval: 循环检查服务器的时间间隔，服务器为active时，退出检查
        :return: 根据管理IP初始化一个服务器对象
        '''
        class show_host_failed(Exception):
            pass
        for i in range(0, check_times):
            result_status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                     % (self.admin_user, self.admin_password, admin_ip))
            if result_status != 'active':
                time.sleep(check_interval)
                i += 1
            if result_status == 'active':
                id = int(self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip)))
                name = self.cmd('''xms-cli -f '{{range .}}{{println .name}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                type = self.cmd('''xms-cli -f '{{range .}}{{println .type}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                roles = self.cmd('''xms-cli -f '{{range .}}{{println .roles}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                public_ips = self.cmd('''xms-cli -f '{{range .}}{{println .public_ips}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                private_ip = self.cmd('''xms-cli -f '{{range .}}{{println .private_ip}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                admin_ip = self.cmd('''xms-cli -f '{{range .}}{{println .admin_ip}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                gateway_ips = self.cmd('''xms-cli -f '{{range .}}{{println .gateway_ips}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                description = self.cmd('''xms-cli -f '{{range .}}{{println .description}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                protection_domain_id = int(self.cmd('''xms-cli -f '{{range .}}{{println .protection_domain.id}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip)))
                status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                up = self.cmd('''xms-cli -f '{{range .}}{{println .up}}{{end}}' --user %s --password %s host list -q "admin_ip:%s"'''
                                % (self.admin_user, self.admin_password, admin_ip))
                return host(id, name, type, roles, public_ips, private_ip, admin_ip, gateway_ips, description, protection_domain_id, status, up)
            if i == check_times:
                raise show_host_failed('循环检查结束，服务器状态为%s' % result_status)
    def DeleteHost(self,host_id, check_times=0, check_interval=0):
        '''
        传入服务器的ID，删除对应的服务器
        :param host_id: 服务器的ID
        :param check_times: 循环检查次数，取值范围：自然数
        :param check_interval: 循环检查时间间隔，单位：秒，取值范围：自然数
        :return:
        '''
        class delete_host_failed(Exception):
            pass

        cmd = 'xms-cli --user %s --password %s host delete %d' % (self.admin_user, self.admin_password, host_id)
        print('下发删除host的命令\n', cmd)
        result = self.cmd(cmd)
        if 'error' in result and check_times == 0:
            print('删除%d号服务器失败\n%s' % (host_id, result))
            return result
        elif check_times > 0:
            for i in range(0, check_times):
                result = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s host list -q "id:%d"''' % (self.admin_user, self.admin_password, host_id))
                if result == '':
                    # 移除对象self
                    print('第%d次检查，删除host成功' % (i + 1))
                    del self
                    break
                if result != '':
                    time.sleep(check_interval)
                    print('第%d次检查，删除host失败，host状态是%s' % ((i + 1), result))
                    i += 1
                elif i == check_times:
                    raise delete_host_failed('循环检查结束，删除%d号host失败' % host_id)
    def CreatePartition(self, disk_list, num, check_times=0, check_interval=0):
        '''
        :param disk_list: 指定SSD的硬盘ID列表，取值范围：列表的每个元素默认是单个数字的字符串，例子：['1','2','3']
        :param num: 每块SSD创建几个缓存分区，取值范围：[2,12]范围的自然数
        :param check_times: 循环检查是否创建成功，检查次数，次数*间隔建议不小于30秒
        :param check_interval: 循环检查是否创建成功，检查间隔，单位：秒
        :return:创建成功的分区id列表
        '''
        partition_list = []
        class create_partition_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s' % (self.admin_user, self.admin_password)
        #由于创建缓存分区的CLI命令下发后，只返回命令下发成功与否，所以不能判断添加缓存分区是否为active
        for i in disk_list:
            cmd2 = partition.create_partition(i, num)
            cmd = cmd1 + cmd2
            result = self.cmd(cmd)
            print('下发创建缓存分区的命令\n%s' % cmd)
            print(result)
            if 'Incorrect' in result:
                raise create_partition_failed('创建缓存分区的命令返回错误')
        for j in disk_list:
            for k in range(0, check_times):
                cmd_str = "xms-cli --user %s --password %s partition list --disk %d| awk '{print $2}'| grep -v ID" % (self.admin_user, self.admin_password, j)
                print('下发查看创建的缓存分区的ID\n%s' % cmd_str)
                result = self.cmd(cmd_str)
                print(result)
                if result == '':
                    print('第%d次检查创建缓存分区，返回ID为空，继续检查' % k)
                    k += 1
                    time.sleep(check_interval)
                if result != '':
                    #将返回结果按\n分片，并转化成单数字字符串组成的列表
                    result = result.split('\n')
                    #去掉列表中重复的''，顺序不变
                    result = sorted(set(result), key=result.index)
                    #去掉列表中最后一个''
                    result.remove('')
                    #把字符串列表转为整型列表
                    for m in range(0, len(result)):
                        for n in result:
                            result.remove(n)
                            result.append(int(n))
                    partition_list = partition_list + result
                    break
                if k == check_times:
                    raise create_partition_failed('循环检查结束，创建%d号盘的缓存分区失败' %j)
        print('创建的缓存分区列表：\n', partition_list)
        return partition_list
    def DeletePartition(self,ssd_disk_list,check_times=0, check_interval=0):
        '''

        :param ssd_disk_list: 创建分区的SSD盘的列表
        :param check_times:
        :param check_interval:
        :return: 删除成功不返回，删除失败返回错误的回显
        '''
        class delete_partition_failed(Exception):
            pass
        for i in ssd_disk_list:
            cmd = 'xms-cli --user %s --password %s partition delete --disk %d' % (self.admin_user, self.admin_password, i)
            result = self.cmd(cmd)
            print(result)
            if '| action_status | active |' in result:
                pass
            else:
                return result
        for i in ssd_disk_list:
            for j in range(0, check_times):
                cmd = 'xms-cli --user %s --password %s partition list --disk %d' % (self.admin_user, self.admin_password, i)
                delete_result = self.cmd(cmd)
                if delete_result == '':
                    print('第%d次检查删除partition状态，删除%d号SSD上的partition成功' % (j, i))
                    break
                if delete_result != '':
                    print('第%d次检查删除partition状态，删除%d号SSD上的partition失败，继续检查，结果为%s' % (j, i, delete_result))
                    time.sleep(check_interval)
                    i += 1
                if 'error' in delete_result or check_times == j:
                    raise delete_partition_failed('第%d次检查删除partition状态，返回错误或者循环次数耗尽' % j)
    def CreateOsd(self, disk_list, cache_partition_list=[], read_cache_size=268435456, role='data', check_times=20, check_interval=10):
        '''
        :param disk_list: 创建osd用到的硬盘ID列表，列表元素取值范围：自然数,例子：[1,2,3,4]
        :param cache_partition: 创建混合盘时用到的缓存分区ID组成的列表，列表元素取值范围：自然数，创建缓存盘时，一个hdd对应一个缓存分区，
        所以创建缓存盘的时候，disk_list和cache_partition列表长度要一样。例子：[11,12,13,14]
        :param read_cache_size: 创建OSD时设置的内存读缓存大小，单位：B，取值范围：不小于134217728（128MB）,默认256MB
        :param role:添加OSD的角色，取值范围：（data|index）二选一，默认:data
        :param check_times:循环检查次数，取值范围：自然数，默认20
        :param check_interval:循环检查时间间隔，单位：秒，取值范围：自然数，默认10
        :return:返回创建成功的osd的ID列表
        '''
        class create_osd_failed(Exception):
            pass
        osd_list1 = []
        osd_list2 = []
        print('缓存分区列表\n%s' % cache_partition_list)
        for i in range(0, len(disk_list)):
            cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
            if cache_partition_list != []:
                cmd2 = osd.create_osd(disk_list[i], cache_partition_list[i], read_cache_size, role)
                print('cmd2\n%s' % cmd2)
            if cache_partition_list == []:
                cmd2 = osd.create_osd(disk_list[i], cache_partition_list, read_cache_size, role)

            cmd3 = " | grep id | grep -v host | grep -v pool | grep -v disk | grep -v osd | grep -v partition | awk '{print $4}'"
            cmd = cmd1 + cmd2 + cmd3
            print('下发添加osd并获取osd的id的命令：\n%s' % cmd)
            result = self.cmd(cmd)
            print(result)
        #这下面的改掉，改成不检查状态；当前采用逐个添加并检查状态，之后添加硬盘采用统一添加后再来检查状态的方式，可以节省一大半时间
            if 'error' in result and check_times == 0:
                return result
            if 'error' in result and check_times != 0:
                raise create_osd_failed('创建osd的命令执行返回错误')
            osd_list1.append(int(result))

        # 循环检查添加硬盘成功
        for j in osd_list1:
            for k in range(0, check_times):
                result = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s osd list -q "id:%d"'''
                                  % (self.admin_user, self.admin_password, j))
                if result != 'active':
                    print('第%d次检查添加%d号OSD状态，时间间隔%d秒，硬盘的状态是%s,继续检查，时间点是' % (k, j, check_interval, result))
                    time.sleep(check_interval)
                    k += 1
                elif result == 'active':
                    print('第%d次检查添加%d号osd状态，时间间隔%d秒，硬盘的状态是%s,添加硬盘成功，时间点是' % (k, j, check_interval, result))
                    osd_list2.append(j)
                    break
                if k == check_times or result == 'building_error':
                    print('第%d次检查添加%d号osd状态，添加osd失败，硬盘状态%s，失败时间点' % (k, j, result))
                    raise create_osd_failed('ID为%d的OSD循环检查状态不通过' % j)
        return osd_list2
    def ShowOsd(self):
        '''

        :param type: OSD的类型，取值范围，HDD,SSD,Hybrid三选一，例子：HDD
        :return: 返回查到的OSD的ID列表
        '''
        result = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s osd list --limit 1000''' % (self.admin_user, self.admin_password))
        osd_list = result.split('\n')
        for i in range(0, len(osd_list)):
            for j in osd_list:
                osd_list.remove(j)
                osd_list.append(int(j))
        osd_list.sort()
        return osd_list
    def SplitOsd(self, osd_list, pool_num, node_num):
        '''
        把传入的OSD，按照节点数node_num均匀分成pool_num份
        :param osd_list:传入的OSD列表，使用限制：只能是同一种类型的OSD，比如SSD_OSD,HDD_OSD,Hybrid_OSD，而且OSD均匀分布在每个节点上，
        关键字不做检查
        :param des_parts_num:希望传入的OSD分成多少份，一般创建多少个POOL，就分成多少份
        :param nodes:服务器的个数，OSD应该尽量均分在节点上，如果集群有6个节点，则填6
        :return:切割好的列表，列表的元素也是列表，比如[[1,2,3],[4,5,6]]
        '''
        class split_osd_failed(Exception):
            pass
        a = []
        buchang = int(len(osd_list)/pool_num/node_num)
        for j in range(0, pool_num):
            b = []
            for i in range(0, len(osd_list), int(len(osd_list)/node_num)):
                b += osd_list[i+j*buchang:i+j*buchang+buchang]
            a.append(b)
        return a
    def DeleteOsd(self,osd_list,check_times=5,check_interval=5):
        '''
        CLI命令只能一个一个删除osd，给关键字传入待删除的osd列表，关键字也是一个一个删
        :param osd_list: 由osd的id组成的列表
        :param check_times: 循环检查是否删除干净，检查次数
        :param check_interval: 循环检查是否删除干净，检查时间间隔
        :return:
        '''
        class delete_osd_failed(Exception):
            pass
        #下发删除osd的命令，一个一个删除
        for i in osd_list:
            cmd = '''xms-cli --user %s --password %s osd delete %d | grep "| status         | " | awk '{print $4}''''' % (self.admin_user, self.admin_user, i)
            result = self.cmd(cmd)
            if result == 'deleting':
                pass
            else:
                raise delete_osd_failed('删除osd失败')
        #删除osd之后，检查是否还能查询到
        for j in osd_list:
            for k in range(0, check_times):
                cmd = 'xms-cli --user %s --password %s osd show %d' % (self.admin_user, self.admin_password, j)
                result = self.cmd(cmd)
                if 'osd not found' in result:
                    print('删除%d号osd成功')
                else:
                    time.sleep(check_interval)
                    k += 1
                if k == check_times:
                    raise delete_osd_failed('循环检查结束，删除%d号osd失败' % j)
    def DeleteDisk(self, disk_id, check_times, check_interval):
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        #根据disk_id获取name
        stdin, stdout, stderr = ssh.exec_command(
            "xms-cli --user %s -p %s osd list |awk '{print  $4,$24}'| grep -w %d |awk '{print $1}'"
            % (self.admin_user, self.admin_password, disk_id))
        osdname = stdout.read().decode()[:-1]
        #根据disk_id获取id
        stdin,stdout,stderr = ssh.exec_command("xms-cli --user admin -p admin osd list |awk '{print  $2,$24}'| grep -w %d |awk '{print $1}'"
                                               % disk_id)
        osdid = stdout.read().decode()[:-1]
        cmd1 = 'xms-cli --user %s --password %s' % (self.admin_user, self.admin_password)
        cmd2 = osd.osd.delete_osd(self, id)
        cmd = cmd1 + ' ' + cmd2 + ' ' + osdid
        print('下发移除硬盘的命令',cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()
        result_err = stderr.read().decode()
        if result_out == '':
            print('删除失败,脚本退出')
            print(result_out)
            exit()
        if result_err != '':
            print('删除失败，脚本退出')
            print(result_err)
            exit()
        for i in range(1, check_times):
            time.sleep(check_interval)
            stdin, stdout, stderr = ssh.exec_command("xms-cli --user %s --password %s osd list | grep %s | awk '{print $8}'"
                                                   % (self.admin_user, self.admin_password, osdname))
            result = stdout.read().decode()[:-1]
            if result == '':
                print('移除硬盘成功')
                break
            if result == 'deleting':
                print('第%d次检查，间隔%d秒，移除硬盘状态是%s，继续' % (i, check_interval, result))
                i += 1
            if i == check_times:
                print('第%d次检查，间隔%d秒，移除硬盘失败，状态是%s' % (i, check_interval, result))
    def GetAllDisk(self,type):
        '''
        传入指定的硬盘类型；从集群所有节点上查找指定类型的所有空闲的非系统盘，返回硬盘的ID列表
        :param type: 硬盘的类型，取值范围：SSH和HDD，二选一
        :return: 硬盘的ID列表
        '''
        result = self.cmd(
            "xms-cli --user %s --password %s disk list | awk -F '|' '{print $2,$6,$8,$10}'| grep 'false   false' | grep %s | awk '{print $1}'"
            % (self.admin_user, self.admin_password, type))
        result_list = result.split('\n')
        try:
            result_list.remove('')
        except:
            pass
        #列表中的元素改成整型，并从小到大排序
        print(result_list)
        for i in range(0, len(result_list)):
            for j in result_list:
                result_list.remove(j)
                result_list.append(int(j))
        result_list.sort()
        return result_list
    def GetDisk(self, host_list, disk_per_host, type):
        '''
        传入指定的服务器，每个服务器出多少块硬盘，硬盘的类型；返回硬盘的id列表
        :param host_list: 出硬盘的服务器列表，列表元素为服务器对象
        :param disk_per_host: 每个节点出多少块盘，取值范围：自然数，一般不大于75
        :param type: 获取硬盘的类型，取值范围：HDD和SSD，二选一
        :return: 盘ID组成的列表，形如：['1','2','3','4','5']
        '''
        disk_id_list = []
        #查看所有系统盘的ID，并组成字符串行列表
        system_disk_id_list = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s disk list -q "is_root:true"'''
                                       % (self.admin_user, self.admin_password))
        system_disk_id_list = re.split('\n', system_disk_id_list)
        try:
            system_disk_id_list.remove('--')
            system_disk_id_list.remove('')
        except:
            pass
        print('show system_disk successfully')
        #在每个节点上获取指定类型和个数的硬盘，组成整型列表
        for i in range(0, len(host_list)):
            cmd1 = "xms-cli --user %s --password %s " % (self.admin_user, self.admin_password)
            cmd2 = """disk list | awk '($6=="%s"){ print $2,$10}' | grep %s | awk '{print $1}'""" % (host_list[i].name, type)
            cmd = cmd1 + cmd2
            out = self.cmd(cmd)

            #正则，按换行符\n切割返回的字符串，并把结果转成列表
            out1 = re.split('\n', out)
            for i in system_disk_id_list:
                try:
                    out1.remove(i)
                except:
                    pass
            out1 = out1[:disk_per_host]
            for i in out1:
                disk_id_list.append(i)
        # disk的id用来创建osd和partition，创建osd和partition只能一个一个disk创建，返回列表比返回字符串要好得多
        # 把列表中的元素改成整型，排序后返回
        for i in range(0, len(disk_id_list)):
            for k in disk_id_list:
                disk_id_list.remove(k)
                disk_id_list.append(int(k))
        disk_id_list.sort()
        print('obtained disk id list：', disk_id_list)
        return disk_id_list
    def CreateClientGroup(self, type, codes, name, description=None, check_times=0, check_interval=0):
        '''

        :param type: 创建客户端组的类型，取值范围：iSCSI，FC二选一
        :param description: 描述，取值范围：字符串
        :param codes: codes,如果是iscsi客户端，则是客户端业务IP或者iqn；如果是FC客户端，没有FC环境，不知道怎么调
        :param name: 客户端组的名称，符合命名规则即可
        :param check_times: 循环检查创建客户端组是否成功，循环次数参数
        :param check_interval: 循环检查创建客户端组是否成功，循环间隔参数
        :return:创建成功返回client_group对象，创建失败返回命令回显
        '''
        class create_clientgroup_failed (Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = client_group.create_client_group(type, description, codes, name)
        cmd = cmd1 + cmd2
        #print('时间点：\n下发创建客户端组的命令：\n',cmd)
        print(cmd)
        result = self.cmd(cmd)
        print(result)
        if 'error' in result:
            print('创建客户端组%s失败' % name)
            return result
        else:
            id = int(re.findall('(?<=\| id               \| )\w*', result)[0])
            for i in range(0, check_times):
                result_status = self.cmd( "xms-cli --user %s --password %s client-group show %d | grep status | awk '{print $4}'" % (self.admin_user, self.admin_password, id))
                if result_status != 'active':
                    time.sleep(check_interval)
                    print('第%d次检查创建客户端组%s状态，时间间隔%d秒，客户端组的状态是%s,继续检查，时间点是' % (i, name, check_interval, result_status))
                    i += 1
                elif result_status == 'active':
                    print('第%d次检查创建客户端组%s状态，时间间隔%d秒，客户端组的状态是%s,创建客户端组成功，时间点是' % (i, name, check_interval, result_status))
                    result = self.cmd('xms-cli --user %s --password %s client-group show %d' % (self.admin_user, self.admin_password, id))
                    client_num = int(re.findall('(?<=\| client_num       \| )\w*',result)[0])
                    access_path_num = int(re.findall('(?<=\| access_path_num  \| )\w*', result)[0])
                    block_volume_num = int(re.findall('(?<=\| block_volume_num \| )\w*', result)[0])
                    return client_group(id, name, type, description, client_num, access_path_num, block_volume_num, result_status, codes)
                if i == check_times:
                    raise create_clientgroup_failed('循环检查结束，创建客户端组%s失败' % name)
    def ShowClientGroup(self, name, check_times=1, check_interval=1):
        '''
        根据传入的客户端组名称，返回对应的客户端组对象
        :param name: 客户端组的名称
        :return: 成功则返回客户端组对象，失败则返回命令回显
        '''
        class show_clientgroup_failed(Exception):
            pass
        #client-group的API没有-q选项，所以用name转成ID查询，来实例client-group对象
        client_group_id = int(self.cmd("xms-cli --user %s --password %s client-group list | awk '{print $2,$4}'| grep %s | awk '{print $1}'" % (self.admin_user, self.admin_password, name)))
        for i in range(0,check_times):
            result = self.cmd('xms-cli --user %s --password %s client-group show %d' % (self.admin_user, self.admin_password, client_group_id))
            result_status = re.findall('(?<=\| status           \| )\S*', result)[0]
            if result_status != 'active':
                print('第%d次检查客户端组状态，状态为%s，继续检查' % (i, result_status))
                time.sleep(check_interval)
                i += 1
            if result_status == 'active':
                id = client_group_id
                name = re.findall('(?<=\| name             \| )\S*', result)[0]
                type = re.findall('(?<=\| type             \| )\S*', result)[0]
                description = re.findall('(?<=\| description      \| )\S*', result)[0]
                client_num = int(re.findall('(?<=\| client_num       \| )\S*', result)[0])
                access_path_num = int(re.findall('(?<=\| access_path_num  \| )\S*', result)[0])
                block_volume_num = int(re.findall('(?<=\| block_volume_num \| )\S*', result)[0])
                status = result_status
                codes_result = self.cmd('''xms-cli -f '{{range .}}{{println .clients}}{{end}}' --user %s --password %s client-group list | grep id:%d''' % (self.admin_user, self.admin_password, id))
                codes = re.findall('(?<= code:)\S*',codes_result)[0]
                return client_group(id, name, type, description, client_num, access_path_num, block_volume_num, status, codes)
            if i == check_times:
                raise show_clientgroup_failed('循环检查结束，客户端组状态为%s' % result_status)
    def CreateAccessPath(self, type, name, tname='', tsecret='', chap='false', description='', check_times=0, check_interval=0):
        '''
        创建访问路径的关键字，由node对象调用
        :param type: 取值范围（iSCSI|FC|Local）三选一
        :param tname: 长度1-223个字符，内容只能包含大小写字母，数字，下划线，点号，冒号，连接符
        :param tsecret: 长度12-16个字符，内容只能包含大小写字母，数字，下划线，点号，冒号，连接符
        :param name: 长度不超过128个字符
        :param chap: 取值范围（true|false）二选一
        :param description: 描述
        :param check_interval: 循环检查时间间隔
        :param check_times: 循环检查次数
        :return:
        '''
        class create_accesspath_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = access_path.create_access_path(type, name, tname, tsecret, chap, description)
        cmd = cmd1 + cmd2
        print('时间点：\n下发创建访问路径的命令：\n', cmd)
        result_out = self.cmd(cmd)
        print(result_out)
        if 'error' in result_out:
            raise create_accesspath_failed('创建访问路径的命令返回错误')
        for i in range(0, check_times):
            result_status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s access-path list -q "name:%s"'''
                                                     %(self.admin_user, self.admin_password, name))
            if result_status != 'active':
                time.sleep(check_interval)
                print('第%d次检查创建访问路径状态，时间间隔%d秒，访问路径的状态是%s,继续检查，时间点是' % (i, check_interval, result_status))
                i += 1
            elif result_status == 'active':
                print('第%d次检查创建访问路径状态，时间间隔%d秒，访问路径的状态是%s,创建访问路径成功，时间点是' % (i, check_interval, result_status))
                result_out = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .type}}{{println .description}}{{println .protection_domain.id}}{{println .block_volume_num}}{{println .client_group_num}}{{println .chap}}{{println .tname}}{{println .tsecret}}{{println .status}}{{println .action_status}}{{println .create}}{{end}}' --user %s --password %s access-path list -q "name:%s"'''
                                      % (self.admin_user, self.admin_password, name))
                result_out = result_out.split('\n')
                id = int(result_out[0])
                name = result_out[1]
                type = result_out[2]
                description = result_out[3]
                protection_domain_id = int(result_out[4])
                volume_num = int(result_out[5])
                client_group_num = int(result_out[6])
                chap = result_out[7]
                tname = result_out[8]
                tsecret = result_out[9]
                status = result_out[10]
                action_status = result_out[11]
                create = result_out[12]
                return access_path(id, name, type, description, protection_domain_id, volume_num, client_group_num, chap, tname, tsecret,
                                               status, action_status, create)

            if i == check_times:
                raise create_accesspath_failed('循环检查结束，创建访问路径%s失败' % name)
    def ShowAccessPath(self, name):
        '''

        :return: 根据名称查询，返回查询到的访问路径对象
        '''
        result = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .type}}{{println .description}}{{println .protection_domain.id}}{{println .volume_num}}{{println .client_group.num}}{{println .chap}}{{println .tname}}{{println .tsecret}}{{println .status}}{{println .action_status}}{{println .create}}{{end}}' --user %s --password %s access-path list -q "name.raw:%s"''' % (self.admin_user, self.admin_password, name))
        result = result.split('\n')
        id = int(result[0])
        name = result[1]
        type = result[2]
        description = result[3]
        protection_domain_id = result[4]
        #volumme_num和client_group_num显示<nil>
        volume_num = result[5]
        client_group_num = result[6]
        chap = result[7]
        tname = result[8]
        tsecret = result[9]
        status = result[10]
        action_status = result[11]
        create = result[12]
        return access_path(id, name, type, description, protection_domain_id, volume_num, client_group_num,
                                       chap, tname, tsecret, status, action_status, create)
    def DeleteAccessPath(self, name, check_times=0, check_interval=0):
        '''
        传入访问路径的名称，删除对应的访问路径，可以循环检查
        :param name: 访问路径的名称
        :param check_times:
        :param check_interval:
        :return: 删除失败，返回命令的回显(只有check_times=0才生效)，
        '''
        class delete_accesspath_failed(Exception):
            pass
        id = int(self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s access-path list -q "name.raw:%s"''' % (self.admin_user, self.admin_password, name)))
        result_status = self.cmd("xms-cli --user %s --password %s access-path delete %d | grep -w status |awk '{print $4}'" % (self.admin_user, self.admin_password, id))
        if result_status == 'deleting':
            pass
        else:
            if check_times == 0:
                return result_status
        for i in range(0, check_times):
            result = self.cmd("xms-cli --user %s --password %s access-path show %d| grep -w status | awk '{print $4}'" % (self.admin_user, self.admin_password, id))
            if 'access_path not found: %d' % id in result:
                break
            if result == 'deleting':
                time.sleep(check_interval)
                i += 1
            if result == 'error' or i == check_times:
                raise delete_accesspath_failed('delete %s access_path failed' %name)
    def CreateMappingGroup(self, block_volumes_ids, access_path, client_group='', check_times=0, check_interval=0):
        '''
        一条映射组里的卷可以对应多个客户端组
        :param block_volumes_ids: 添加到映射的卷ID列表
        :param access_path: 访问路径的ID
        :param client_group:客户端的id，通过CLI命令查询，Local类型的访问路径，默认空;iSCSI和FC必带
        :param check_times:
        :param check_interval:
        :return:命令下发失败，返回错误的回显；命令下发成功，返回映射组对象
        '''
        class create_mappinggroup_failed(Exception):
            pass
        #将传入的整型列表转成字符串
        for i in range(0, len(block_volumes_ids)):
            for j in block_volumes_ids:
                block_volumes_ids.remove(j)
                block_volumes_ids.append(str(j))
        block_volumes_ids = ','.join(block_volumes_ids)
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        #因为命令中只能跟ID，是一个数，查ID太麻烦了，最好能直接用访问路径对象的形式传入，在关键字里对象.id来获取id，
        #然后远程调用create_mapping_group比较好
        cmd2 = mapping_group.create_mapping_group(block_volumes_ids, access_path, client_group)
        cmd = cmd1 + cmd2
        print('下发创建映射组的命令:\n',cmd)
        result = self.cmd(cmd)
        print(result)
        if 'error' in result:
            print('下发创建映射组的命令返回错误，返回错误的回显\n%s' %result)
            return result
        else:
            id = int(re.findall('(?<=\| id                \| )\w*', result)[0])

        #查看mapping_group的状态
        for i in range(0, check_times):
            time.sleep(check_interval)
            result_status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s mapping-group list -q "id:%d"'''
                                     % (self.admin_user, self.admin_password, id))
            if result_status == 'active':
                print('循环检查结束，创建%s号映射组成功' % id)
                id = id
                result = self.cmd('''xms-cli -f '{{range .}}{{println .access_path.id}}{{println .access_path.name}}{{println .status}}{{println .create}}{{end}}' --user %s --password %s mapping-group list -q "id:%d"'''
                                  % (self.admin_user, self.admin_password, id))
                result = result.split('\n')
                access_path_id = int(result[0])
                access_path_name = result[1]
                status = result[2]
                create_time = result[3]
                result_client = self.cmd('xms-cli --user %s --password %s mapping-group show %d' % (self.admin_user, self.admin_password, id))
                try:
                    client_group_id = int(re.findall('(?<=\| client_group.id   \| )\w*', result_client)[0])
                    client_group_name = re.findall('(?<=\| client_group.name \| )\w*', result_client)[0]
                except:
                    client_group_id = ''
                    client_group_name = ''
                return mapping_group(id, access_path_id, access_path_name, client_group_id, client_group_name, status, create_time)
            elif result_status != 'active':
                time.sleep(check_interval)
                print('第%d次检查，检查间隔%d秒，创建映射组失败，状态是%s' % (i, check_interval, result_status))
                i += 1
            if i == check_times or result_status == 'error':
                raise create_mappinggroup_failed('循环检查结束，创建%d号映射组失败，状态为%s' % (id, result_status))
    def ShowMappinggroup(self,access_path_name):
        '''
        根据访问路径的名称查看添加进来的映射组，返回映射组对象组成的列表
        :param access_path_name: 访问路径的名称
        :return: 映射组对象组成的列表
        '''
        class show_mappinggroup_failed(Exception):
            pass
        mappinggroup_list = []
        cmd = """xms-cli --user %s --password %s mapping-group list | awk -F '|' '{print $2,$3,$4,$5,$6,$7,$8}'| awk '($3=="%s"){ print}'"""\
              % (self.admin_user, self.admin_password, access_path_name)
        result = self.cmd(cmd)
        if result == '':
            raise show_mappinggroup_failed('指定的访问路径中不存在映射组')
        else:
            #用返回结果中的字段作为初始化映射组对象的参数
            result = result.split(' ')
            for i in range(0, result.count('')):
                result.remove('')
            for i in range(0, result.count('\n')):
                result.remove('\n')
            for i in range(0, len(result), 7):
                id = int(result[i])
                access_path_id = int(result[i + 1])
                access_path_name = result[i + 2]
                client_group_name = result[i + 4]
                status = result[i + 5]
                create = result[i + 6]
                try:
                    client_group_id = int(result[i + 3])
                    if client_group_name == '<nil>':
                        client_group_name = ''
                except:
                    client_group_id = ''
                mappinggroup_list.append(mapping_group(id, access_path_id, access_path_name, client_group_id, client_group_name, status, create))
        return mappinggroup_list
    def DeleteMappinggroup(self, mg_id, check_times=0, check_interval=0):
        '''
        传入映射组的ID，删除映射组
        :param mg_id: 映射组的ID
        :param check_times: 循环检查次数，取值范围：自然数
        :param check_interval: 循环检查时间间隔，单位：秒，取值范围：自然数
        :return: 如果删除失败，返回命令的回显；如果删除成功，没有返回，返回None
        '''
        class delete_mappinggroup_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = 'mapping-group delete %d' % mg_id
        cmd = cmd1 + cmd2
        print('下发删除映射组的命令\n%s' % cmd)
        result = self.cmd(cmd)
        if 'error' in result and check_times == 0:
            return result
        else:
            for i in range(0, check_times):
                while 'still has IO on target' in result:
                    time.sleep(check_interval)
                    print('重试下发删除mapping-group的命令\n', cmd)
                    result = self.cmd(cmd)
                    print result
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s mapping-group list -q "id:%d"''' \
                  % (self.admin_user, self.admin_password, mg_id)
            result = self.cmd(cmd)
            if result == '':
               #移除对象self
                print('第%d次检查，删除映射组成功' %(i+1))
                del self
                break
            if result != '':
                time.sleep(check_interval)
                print('第%d次检查，删除映射组失败，移除后，映射组状态是%s' %((i+1), result))
                i += 1
            elif i == check_times:
                raise delete_mappinggroup_failed('循环检查结束，删除%d号映射组失败' % mg_id)
    def SetVolume(self,volume_id, check_times=0, check_interval=0,  **kwargs):
        '''
        由volume对象调用，传入参数修改卷对象，循环检查每项修改后的值和传入值是否一致，循环结束才能修改对象特性值
        :param volume_id: 要修改的某个卷的ID
        :param name: 修改卷，卷的新名称，取值范围：字符串
        :param size: 卷大小，单位：B，取值范围：自然数
        :param flattened:抹平卷，取值范围：字符串，true|flase二选一
        :param performance_priority: 性能优先级，取值范围：自然数，0|1二选一
        :param qos_enabled:qos开关，取值范围：字符串，true|false二选一
        :param max_total_iops:qos_enable为true时才生效，取值范围：自然数
        :param max_total_bw:qos_enable为true时才生效，取值范围：自然数
        :param burst_total_iops:qos_enable为true时才生效，取值范围：自然数
        :param burst_total_bw:qos_enable为true时才生效，取值范围：自然数
        :param description:取值范围：字符串
        :param check_times:循环检查修改是否成功，检查次数，取值范围：自然数
        :param check_interval:循环检查修改是否成功，检查时间间隔，单位：秒，取值范围：自然数
        :return: 下发错误，返回命令回显；下发成功，循环检查确保字段都修改成功（修改对象的字段），如果要拿到一个新volume对象，请修改后调ShowVolume
        '''
        class set_volume_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = 'block-volume set'
        cmd3 = ''
        cmd4 = ' %d' % volume_id
        for i in kwargs:
            print('传入的属性名称', i)
            print('传入的属性的类型', type(kwargs.get(i)))
            print('传入的属性值', kwargs.get(i))
            if '_' in i:
                m = re.sub('_', '-', i)
            else:
                m = i
            #python2.7中的整型分为long型和int型
            if isinstance(kwargs.get(i), int) or isinstance(kwargs.get(i), long):
                cmd3 = cmd3 + ' --' + m + '=%d' % kwargs.get(i)
            if isinstance(kwargs.get(i), str):
                cmd3 = cmd3 + ' --' + m + '=%s' % kwargs.get(i)
        cmd  = cmd1 + cmd2 + cmd3 + cmd4
        print('execute change volume command\n', cmd)
        result = self.cmd(cmd)
        print(result)
        if 'Incorrect Usage' in result or 'error' in result:
            return result
        for j in list(set(kwargs.keys()).intersection(set(['name', 'flattened', 'qos_enabled', 'description']))):
            for k in range(0, check_times):
                result = self.cmd('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (j, self.admin_user, self.admin_password, volume_id))
                if result == kwargs.get(j):
                    print('修改%s属性成功,新值%s' % (j, result))
                    break
                if result != kwargs.get(j):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，不同' % (k, j, result, kwargs.get(j)))
                    k += 1
                    time.sleep(check_interval)
                if k == check_times:
                    raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s,而传入为%s不一致' %(volume_id,j,result,kwargs.get(j)))
        # 查询修改后的特性是否和传入的参数值一致，size和performance_priority的值为整型自然数，API中字段和CLI字段一致，所以放在一组
        #API查出来的容量单位是B，所以用关键字的时候，只接受B为单位，提过改进建议，结论不修改
        for l in list(set(kwargs.keys()).intersection(set(['size', 'performance_priority']))):
            for k in range(0, check_times):
                result = self.cmd('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (l, self.admin_user, self.admin_password, volume_id))
                result = int(result)
                if result == kwargs.get(l):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，相同' % (k, l, result, kwargs.get(l)))
                    break
                if result != kwargs.get(l):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，不同' % (k, l, result, kwargs.get(l)))
                    k += 1
                    time.sleep(check_interval)
                if k == check_times:
                    raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s,而传入为%s不一致' % (volume_id, l, result, kwargs.get(l)))
        # 查询修改后的特性是否和传入的参数值一致，max_total_iops,max_total_bw,burst_total_iops,burst_total_bw的值为整型自然数，API中字段和CLI字段不一致，所以放在一组
        qos_list = list(set(kwargs.keys()).intersection(set(['max_total_iops','max_total_bw','burst_total_iops','burst_total_bw'])))
        for m in qos_list:
            for k in range(0, check_times):
                result = self.cmd(
                    '''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (m, self.admin_user, self.admin_password, volume_id))
                result = int(result)
                if result == kwargs.get(m):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，相同' % (k, m, result, kwargs.get(m)))
                    break
                if result != kwargs.get(m):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，相同' % (k, m, result, kwargs.get(m)))
                    k += 1
                    time.sleep(check_interval)
                if k == check_times:
                    raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s,而传入为%s不一致' % (volume_id, m, result, kwargs.get(m)))
    def DeleteVolume(self,volume_id,check_times=0,check_interval=0):
        '''
        传入卷的ID，删除对应的卷
        :param volume_id: 卷的ID，int或者long
        :param check_times: 循环检查次数，取值范围：自然数
        :param check_interval: 循环检查时间间隔，单位：秒，取值范围：自然数
        :return:
        '''
        class delete_volume_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        cmd2 = 'block-volume delete %d' % volume_id
        cmd = cmd1 + cmd2
        print('下发删除卷的命令\n%s' % cmd)
        result = self.cmd(cmd)
        if 'error' in result:
            return result
        # 判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' \
                  % (self.admin_user, self.admin_password, volume_id)
            result = self.cmd(cmd)
            if result == '':
                print('第%d次检查，删除%d号卷成功' % (i + 1,volume_id))
                break
            if result != '':
                time.sleep(check_interval)
                print('第%d次检查，删除%d号卷失败，卷状态是%s' % ((i + 1), volume_id, result))
                i += 1
            elif result == 'error' or i == check_times:
                raise delete_volume_failed('循环检查结束，删除%d号卷失败，状态为%s，循环总次数%d，已用次数%d' % (volume_id, result, check_times, i))
    def CreateTarget(self,access_path,host,check_times=0,check_interval=0):
        '''
        给访问路径添加网关服务器的关键字
        :param access_path: 访问路径ID
        :param host: 网关服务器服务器的ID
        :param check_times: 循环检查添加成功的次数
        :param check_interval: 循环检查添加成功的时间间隔
        :return: 命令下发失败返回错误的回显；循环检查成功返回target对象
        '''
        class create_target_failed(Exception):
            pass
        cmd1 = 'xms-cli --user %s --password %s ' % (self.admin_user, self.admin_password)
        print(cmd1)
        # 因为命令中只能跟ID，是一个数，查ID太麻烦了，最好能直接用访问路径对象的形式传入，在关键字里对象.id来获取id，
        # 然后远程调用target比较好
        cmd2 = target.create_target(access_path, host)
        print(cmd2)
        cmd = cmd1 + cmd2
        print('下发添加网关服务器的命令:\n', cmd)
        result_out = self.cmd(cmd)
        if 'error' in result_out:
            return result_out
        else:
            id = int(re.findall('(?<=\| id             \| )\w*',result_out)[0])
        # 查看mapping_group的状态
        for i in range(0, check_times):
            result_status = self.cmd('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s target list -q "id:%d"'''
                % (self.admin_user, self.admin_password, id))
            if result_status == 'active':
                print('第%d次检查，检查间隔%d秒，添加%s号网关服务器添加%s号网关服务器成功，状态是%s' %(i, check_interval, access_path,host,result_status))
                out = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .host.id}}{{println .board}}{{println .port}}{{println .iqn}}{{println .access_path.id}}{{println .status}}{{println .create}}{{end}}' --user %s --password %s target list -q "id:%d"'''
                                      %(self.admin_user,self.admin_password,id))
                out = out.split('\n')
                id = int(out[0])
                host_id = int(out[1])
                board = int(out[2])
                port = int(out[3])
                iqn = out[4]
                access_path_id = int(out[5])
                status = out[6]
                create = out[7]
                return target(id, host_id, board, port, iqn, access_path_id, status, create)
            elif result_status != 'active':
                time.sleep(check_interval)
                print('第%d次检查，检查间隔%d秒，创建映射组失败，状态是%s' % (i, check_interval, result_status))
                i += 1
            if i == check_times:
                print('第%d次检查，创建target失败' % i)
                raise create_target_failed('循环检查结束，给%d号访问路径添加的%d号网关服务器状态为%s' %(access_path,host,result_status))
    def ShowTarget(self,access_path_name):
        '''
        返回指定访问路径上的网关服务器对象组成的列表
        :param access_path_name: 访问路径的名称
        :return:
        '''
        class show_target_failed(Exception):
            pass
        target_object_list = []
        cmd = '''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s target list -q "access_path.name.raw:%s"''' % (self.admin_user, self.admin_password, access_path_name)
        target_id_list = self.cmd(cmd)
        try:
            target_id_list = target_id_list.split('\n')
        except:
            pass
        for i in range(0, len(target_id_list)):
            for j in target_id_list:
                target_id_list.remove(j)
                target_id_list.append(int(j))
        for k in target_id_list:
            result = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .host.id}}{{println .board}}{{println .port}}{{println .iqn}}{{println .access_path.id}}{{println .status}}{{println .create}}{{end}}' --user %s --password %s target list -q "id:%d"''' %(self.admin_user,self.admin_password,k))
            try:
                result = result.split('\n')
            except:
                pass
            id = int(result[0])
            host_id = int(result[1])
            board = int(result[2])
            port = int(result[3])
            iqn = result[4]
            access_path_id = int(result[5])
            status = result[6]
            create = result[7]
            target_obj = target(id, host_id, board, port, iqn, access_path_id, status, create)
            target_object_list.append(target_obj)
        return target_object_list
    def DeleteTarget(self, ap_id,host_id, check_times=0, check_interval=0):
        '''
        传入ap和节点的ID，删除对应的target，比如ap-123和node1的ID，删除node1作的target
        :param ap_id: 访问路径的ID
        :param host_id: 节点的ID
        :param check_times: 循环检查次数
        :param check_interval: 循环检查时间间隔，单位：秒
        :return:
        '''
        class delete_target_failed(Exception):
            pass
        cmd = '''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s target list -q "access_path.id:%d"''' % (self.admin_user, self.admin_password, ap_id)
        print('下发查询%d号AP上网关服务器的命令%s\n' % (ap_id, cmd))
        #单AP上多个target，获取到的是ID列表
        id_list = self.cmd(cmd)
        id_list = id_list.split('\n')
        for i in range(0, len(id_list)):
            for j in id_list:
                id_list.remove(j)
                id_list.append(int(j))
        for i in id_list:
            cmd = '''xms-cli -f '{{range .}}{{println .host.id}}{{end}}' --user %s --password %s target list -q "id:%d"''' % (self.admin_user, self.admin_password, i)
            print(cmd)
            host_id_1 = self.cmd(cmd)
            if host_id == int(host_id_1):
                target_id = i
                cmd_1 = "xms-cli --user %s --password %s target delete %d | grep -w status | awk '{print $4}'" % (self.admin_user, self.admin_password, i)
                print('下发移除网关服务器的命令\n', cmd_1)
                result = self.cmd(cmd_1)
                print(result)
        if result != 'deleting':
            return result
        else:
            pass
        #循环检查删除结果，target的CLI没有show选项
        for i in range(0,check_times):
            delete_result = self.cmd("""xms-cli --user %s --password %s target list | awk '($2=="%d"){print $14}'""" %(self.admin_user, self.admin_password, target_id))
            if delete_result == '':
                print('第%d次检查移除网关服务器结果，时间间隔%d秒，移除成功' %(i,check_interval))
                break
            if 'deleting' in delete_result:
                time.sleep(check_interval)
                print('第%d次检查移除网关服务器结果，时间间隔%d秒，状态为%s' % (i, check_interval, delete_result))
                i += 1
            if delete_result == 'error' or i == check_times:
                raise delete_target_failed('移除网关服务器，状态为%s,循环总次数为%d，已用次数为' % (delete_result, check_times, i))

    # def check_badio(self):
    #
    # def check_consistent(self):
    #def CompareData(file1,file2):
    def xdcadm_api(self,L='at',m='at',o='show',t=None,l=None,n=None,v=None,i=None,s=None,b=None,T=None,P=None,N=None,U=None,S=None,C=None,u=None,p=None,I=None,O=None,h=None,V=None):
        '''
        参数是真的多,xdcadm -h查看各个参数的用法
        :param L: 只有一个取值at，表示access target
        :param m:取值范围（at,target,lun,client,system）
        :param o:取值范围（create,delete,add,remove,show,update,save,load）
        :param t:atid,取值范围：自然数
        :param l:小写的"L"，lun_id
        :param n:name，系统配置选项，取值范围：debug/pref_read/log_level
        :param v:value for config debug/pref_read/log_level
        :param i:iqn，启动器或者目标器的iqn
        :param s:servernode，取值范围（servernode or at）
        :param b:boardid is 0-1 for access target
        :param T:type for target iSCSI/local/FC
        :param P:目标器的IP:port，比如127.0.0.1:3260
        :param N:lun_name
        :param U:lun_sn
        :param S:lun_size
        :param C:luncfg,取值范围:ceph/poolname/imagename
        :param u:user for chap
        :param p:password for chap
        :param I:incoming for chap,target account
        :param O:outgoing for chap,initiator account
        :param h:xdcadm help
        :param V:xdcadm version
        :return:命令返回的字符串
        '''
        #拼接命令
        class xdcapi_call_failed(Exception):
            pass
        cmd = 'xdcadm -L %s -m %s -o %s' % (L, m, o)
        print('下发xdcadm查询命令\n',cmd)
        result = self.cmd(cmd)
        print(result)

    def check_status(self, cmd, check_entry, relate, expect_value='', check_times=0, check_interval=0):
        '''
        :param cmd: 下发的查询命令，可以直接写shell命令，也可以调关键字，比如pool.show_pool
        :param check_entry: 返回结果中的需要观察的字段，比如空间回收测试中，pool的容量
        :param relate: 观察字段和预期值的比较关系，暂时这些，=，!=，>，<，>=，<=，is None，is not None，（没有字符串的in，not in，
        这两个可以用<和其它判断符号代替，其它的我还没找到）
        :param expect_value:可以是任何值，包括空值，如果检查status，expect_value可以是active,builing,initializing，如果检查
        capacity，expect_value可以是1GB，100GB，默认为空
        :param check_times:循环检查次数，默认不循环
        :param check_interval:循环检查时间间隔，默认不循环，单位：秒
        :return:比较成功会返回1，脚本继续；最终比较失败，脚本抛异常；中途比较成功一次，最终比较失败，也会抛异常
        '''
        class check_status_failed(Exception):
            pass
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()
        check_entry_1 = '(?<= %s: )\S*' % check_entry
        #获取字段，返回结果是值组成的列表
        try:
            get_value = re.findall(check_entry_1, result_out)
        except:
            raise check_status_failed('查询字段的值失败')
    def Cleanup(self):
        '''
        清理环境关键字，节点执行后，删除所有配置，只保留主节点一个。在脚本的第一步初始化和最后一步恢复初始化状态用
        客户端的清理功能由客户端的cleanup完成
        清除ap,mg，pool，volume等操作，没有时间限制，如果清环境失败会一直卡住
        当前只从1级快照开始删，如果有克隆和复制，是清不掉的
        :return:如果删除成功，没有返回，如果删除失败，返回错误的回显，并报异常
        '''
        class cleanup_failed(Exception):
            pass
        #删除所有的映射组
        print('clean-test')
        try:
            mg_id = self.cmd("xms-cli --user admin --password admin mapping-group list | awk '{print $2}'| grep -v ID")
            mg_id = mg_id.split('\n')
            mg_id = sorted(set(mg_id), key=mg_id.index)
            mg_id.remove('')
            for i in mg_id:
                cmd = "xms-cli --user admin --password admin mapping-group delete %s" % i
                print('下发删除mapping-group的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while 'still has IO on target' in result:
                time.sleep(5)
                cmd = "xms-cli --user admin --password admin mapping-group delete %s" % i
                print('下发删除mapping-group的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin mapping-group list') != '':
                print('等待删除mg成功')
                time.sleep(5)
        except:
            pass
        #删除所有的网关服务器
        try:
            tg_id = self.cmd("xms-cli --user admin --password admin target list | awk '{print $2}'| grep -v ID")
            tg_id = tg_id.split('\n')
            tg_id = sorted(set(tg_id), key=tg_id.index)
            tg_id.remove('')
            for i in tg_id:
                cmd = "xms-cli --user admin --password admin target delete %s" % i
                print('下发删除target的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin target list') != '':
                print('等待删除tg成功')
                time.sleep(5)
        except:
            pass
        #删除所有访问路径
        try:
            ap_id = self.cmd("xms-cli --user admin --password admin access-path list | awk '{print $2}'| grep -v ID")
            ap_id = ap_id.split('\n')
            ap_id = sorted(set(ap_id), key=ap_id.index)
            ap_id.remove('')
            for i in ap_id:
                cmd = "xms-cli --user admin --password admin access-path delete %s" % i
                print('下发删除access-path的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin access-path list') != '':
                print('等待删除ap成功')
                time.sleep(5)
        except:
            pass
        #删除所有客户端组
        try:
            cg_id = self.cmd("xms-cli --user admin --password admin client-group list | awk '{print $2}'| grep -v ID")
            cg_id = cg_id.split('\n')
            cg_id = sorted(set(cg_id), key=cg_id.index)
            cg_id.remove('')
            for i in cg_id:
                cmd = "xms-cli --user admin --password admin client-group delete %s" % i
                print('下发删除client-group的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin client-group list') != '':
                print('等待删除cg成功')
                time.sleep(5)
        except:
            pass
        #删除所有快照
        try:
            snap_id = self.cmd("xms-cli --user admin --password admin block-snapshot list | awk '{print $2}'| grep -v ID")
            snap_id = snap_id.split('\n')
            snap_id = sorted(set(snap_id), key=snap_id.index)
            snap_id.remove('')
            for i in snap_id:
                cmd = "xms-cli --user admin --password admin block-snapshot delete %s" % i
                print('下发删除block-snapshot的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin block-snapshot list') != '':
                print('等待删除snap成功')
                time.sleep(5)
        except:
            pass
        #删除所有卷
        try:
            volume_id = self.cmd("xms-cli --user admin --password admin block-volume list | awk '{print $2}'| grep -v ID")
            volume_id = volume_id.split('\n')
            volume_id = sorted(set(volume_id), key=volume_id.index)
            volume_id.remove('')
            for i in volume_id:
                cmd = "xms-cli --user admin --password admin block-volume delete %s" % i
                print('下发删除block-volume的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin block-volume list') != '':
                print('等待删除volume成功')
                time.sleep(5)
        except:
            pass
        #删除所有pool
        try:
            pool_id = self.cmd("xms-cli --user admin --password admin pool list | awk '{print $2}'| grep -v ID")
            pool_id = pool_id.split('\n')
            pool_id = sorted(set(pool_id), key=pool_id.index)
            pool_id.remove('')
            for i in pool_id:
                cmd = "xms-cli --user admin --password admin pool delete %s" % i
                print('下发删除pool的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            while self.cmd('xms-cli --user admin --password admin pool list') != '':
                print('等待删除pool成功')
                time.sleep(5)
        except:
            pass
        #删除所有OSD
        try:
            osd_id = self.cmd("xms-cli --user admin --password admin osd list | awk '{print $2}'| grep -v ID")
            osd_id = osd_id.split('\n')
            osd_id = sorted(set(osd_id), key=osd_id.index)
            osd_id.remove('')
            for i in osd_id:
                cmd = "xms-cli --user admin --password admin osd delete %s" % i
                print('下发删除osd的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
                while 'Can not delete osd with action status updating' in result:
                    result = self.cmd(cmd)
            while self.cmd('xms-cli --user admin --password admin osd list') != '':
                print('等待删除osd成功')
                time.sleep(5)
        except:
            pass
        #删除所有缓存分区，由于partition的CLI需要带SSD_DISK_ID才能list，所以先获取SSD的ID
        try:
            partition_list = []
            ssd_disk_id_list = self.cmd("xms-cli --user admin --password admin disk list | grep SSD |awk '{print $2}'")
            ssd_disk_id_list = ssd_disk_id_list.split('\n')
            #获取所有的缓存分区的ID
            for i in ssd_disk_id_list:
                cmd = 'xms-cli --user admin --password admin partition delete --disk=%s' % i
                print('下发删除缓存分区的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            for i in ssd_disk_id_list:
                while self.cmd('xms-cli --user admin --password admin partition list --disk=%s' % i) != '':
                    print('等待删除partition成功')
                    time.sleep(3)
        except:
            pass
        #删除主节点外的服务器
        try:
            host_id = self.cmd("xms-cli --user admin --password admin host list | awk '{print $2}'| grep -v ID")
            host_id = host_id.split('\n')
            host_id = sorted(set(host_id), key=host_id.index)
            host_id.remove('')
            host_id.remove('1')
            for i in host_id:
                cmd = "xms-cli --user admin --password admin host delete %s" % i
                print('下发删除host的命令\n%s' % cmd)
                result = self.cmd(cmd)
                print(result)
            for i in host_id:
                while "host not found: %s" % i not in self.cmd('xms-cli --user admin --password admin host show %s' % i):
                    print('等待删除host成功')
                    time.sleep(5)
        except:
            pass
    def close(self):
        self.transport.close()
        del self

if __name__ == '__main__':
    ips = ["10.0.11.122","10.0.11.121","10.0.11.123"]
    test = EBS()
    t = test.Ping(ips)
    print t

    # node1 = NODE(ip=testbed.cluster2[1][0], user=testbed.cluster2[4], password=testbed.cluster2[5],
    #                   admin_user=testbed.cluster2[6], admin_password=testbed.cluster2[7], cluster='cluster2', port=22)
    # host1 = node1.connect()
    # mg_list1 = node1.ShowMappingGroup('access-path-1')
    # print('映射组的长度是', len(mg_list1))
    # print('映射组的属性是', mg_list1[0].id, mg_list1[1].id)
    # host2 = node1.CreateHost(type='storage_server', roles='block_storage_gateway', public_ip=testbed.cluster2[3][1],
    #                          private_ip=testbed.cluster2[0][1],
    #                          gateway_ip=testbed.cluster2[2][1], admin_ip=testbed.cluster2[1][1], check_times=60,
    #                          check_interval=10)
    # host2 = node1.CreateHost(type='storage_server', roles='block_storage_gateway', public_ip='10.252.2.82',
    #                          private_ip='10.252.1.82',gateway_ip='10.252.2.82', admin_ip='10.252.3.82', check_times=60,check_interval=10)
    # print('roles',host2.roles)
    # print('等待60秒')
    # host2.show_host()
    # print('roles',host2.roles)
    # result = node1.GetDisk([1,4,5],2,'SSD')
    # target_list = node1.ShowTarget('ap3')
    # print(len(target_list))
    # print('1',target_list[0].id)
    # print('2', target_list[1].id)
    # print('3', target_list[2].id)
    # for i in target_list:
    #     i.delete()
    #     # print(result)
    # result = node1.GetAllDisk('HDD')
    #     # print(result)
    # result = node1.CreatePool(osds='81,82,83,84,85,86,87,88',name='POOL3',type='erasure',check_times=25,check_interval=5)
    # print(result.name)
    # result[65,78] == 'has been used'
    # #print(POOL1.CreateVolume(3,4))
    # node1.CreateHost(type='storage_server',roles='block_storage_gateway',public_ip='10.255.101.135',private_ip='10.255.101.135',
    #               gateway_ip='10.255.101.135',admin_ip='10.255.101.135',check_times=60,check_interval=10)
    #disk_list = node1.GetAllDisk('SSD')
    # print(disk_list)
    # for i in disk_list:
    #     node1.CreateOsd(disk=i,cache_partition='',read_cache_size='',role='data',check_times=10,check_interval=10)
    # for i in disk_list:
    #     node1.DeleteDisk(disk_id=i,check_times=10,check_interval=5)
    # # obj.cmd('df -Th')
    # # print(node1.cmd('df -Th'))
    # # obj.put()
    # node1.check_ceph_status()
    # node1.DeletePool(name='POOL1',force='yes',check_times=10,check_interval=10)
    # node1.check_ceph_status()
    #
    # cg1 = node1.CreateClientGroup(type='iSCSI', description='ymd', codes='1.1.1.5,1.1.1.6,1.1.1.7,1.1.1.8', name='rubbish', check_times=10, check_interval=5)
    # print(cg1.codes)
    # node1.DeleteClientGroup(name='rubbish',check_times=5,check_interval=5)
    # node1.CreateAccessPath(type='iSCSI',name='name',tname='tname',tsecret='tsecret',chap='false',description='test',check_times=3,check_interval=3)
    # node1.DeleteAccessPath(name='name',check_times=5,check_interval=2)


    # node1.close()

