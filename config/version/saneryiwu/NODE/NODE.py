# coding=utf-8
import paramiko
#from config.XebsException import ceph_status_error
import sys
sys.path.append('..')
reload(sys)
sys.setdefaultencoding("utf-8")
import socket
from config.version.saneryiwu.POOL import pool as pool
import config.version.saneryiwu.HOST.host as host
import config.version.saneryiwu.OSD.osd as osd
import config.version.saneryiwu.CLIENT_GROUP.client_group as client_group
import config.version.saneryiwu.ACCESS_PATH.access_path as access_path
import config.version.saneryiwu.MAPPING_GROUP.mapping_group as mapping_group
import config.version.saneryiwu.TARGET.target as target
import config.version.saneryiwu.PARTITION.partition as partition
import time
import re
class NODE(object):

    # def __init__(self, ip, port, user, password, admin_user='admin', admin_password='admin', cluster='cluster2'):
    #def __init__(self, cluster=testbed.cluster2):
        # self.ip = ip
        # self.port = port
        # self.user = user
        # self.password = password
        # self.admin_user = admin_user
        # self.admin_password = admin_password
        # self.cluster = cluster

    def connect(self):
        class connect_cluster_failed(Exception):
            pass
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        print('登录节点%s，端口%s，用户名%s，密码%s' % (self.ip, self.port, self.user, self.password))
        result = self.cmd('xms-cli --user %s --password %s host show 1' % (self.admin_user, self.admin_password))
        id = int(re.findall('(?<=\| id                   \| )\w*', result)[0])
        name = re.findall('(?<=\| name                 \| )\S*', result)[0]
        type = re.findall('(?<=\| type                 \| )\S*', result)[0]
        roles = re.findall('(?<=\| roles                \| )\S*', result)[0]
        public_ips = re.findall('(?<=\| public_ips           \| )\S*', result)[0]
        private_ip = re.findall('(?<=\| private_ip           \| )\S*', result)[0]
        admin_ip = re.findall('(?<=\| admin_ip             \| )\S*', result)[0]
        gateway_ips = re.findall('(?<=\| gateway_ips          \| )\S*', result)[0]
        description = re.findall('(?<=\| description          \| )\S*', result)[0]
        protection_domain_id = int(re.findall('(?<=\| protection_domain.id \| )\w*', result)[0])
        status = re.findall('(?<=\| status               \| )\w*', result)[0]
        up = re.findall('(?<=\| up                   \| )\w*', result)[0]
        cluster = self.cluster
        return host.host(id, name, type, roles, public_ips, private_ip, admin_ip, gateway_ips, description, protection_domain_id, status, up, cluster)



    def cmd(self, cmd):
        class cmd_execute_faild(Exception):
            pass
        #重试次数
        retry_times = 10
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd)
        except socket.error as e:
            print('NODE61行，出现socker.error')
            ssh._transport = self.transport
            stdin, stdout, stderr = ssh.exec_command(cmd)
        resultout = stdout.read().decode()[:-1]
        resulterr = stderr.read().decode()[:-1]
        #用不存在的osd和缺少名称的命令创建pool，返回结果中的out和err都不为空，都返回
        if resulterr == '' and resultout != '':
            return resultout
        elif resulterr != '' and resultout != '':
            return resulterr + resultout
        elif resulterr == '' and resultout == '':
            return None
        elif resulterr != '' and resultout == '':
            return resulterr
        ssh.close()

    def put(self, server_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(local_path, server_path)
    def get(self, server_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.get(server_path, local_path)
    def check_ceph_status(self):
        class ceph_err(Exception):
            pass
        result_status = self.cmd("ceph -s| grep health | awk {'print $2'}")
        if result_status == 'HEALTH_OK':
            print('集群状态正常，状态是', result_status)
            return 1
        else:
            raise ceph_err('ceph状态为%s' % result_status)

    def CreatePool(self, osds, name, pool_type='replicated', size=2, pool_role='data', failure_domain_type='host',
                   data_chunk_num=2, coding_chunk_num=1, check_times=0, check_interval=0):
        '''
        :param osds: 必选，创建存储池用到的osd的列表
        :param pool_type: 必选，（replicated|erasure）二选一，默认：replicated
        :param size:如果pool_type为replicated则必选，取值范围：自然数（1-6），默认：2
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
        for i in range(0,len(osds)):
            for j in osds:
                osds.remove(j)
                osds.append(str(j))
        osds = ','.join(osds)
        cmd2 = pool.pool.create_pool(self, osds, pool_type, size, pool_role, failure_domain_type, name, data_chunk_num, coding_chunk_num)
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
                id = int(self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                  % (self.admin_user, self.admin_password, name)))
                name = name
                protection_domain_id = self.cmd('''xms-cli -f '{{range .}}{{println .protection_domain.id}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                                % (self.admin_user, self.admin_password, name))
                protection_domain_id = int(protection_domain_id)
                replicate_size = self.cmd('''xms-cli -f '{{range .}}{{println .replicate_size}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
                                          % (self.admin_user, self.admin_password, name))
                replicate_size = int(replicate_size)
                pool_type = self.cmd('''xms-cli -f '{{range .}}{{println .pool_type}}{{end}}' --user %s --password %s pool list -q "name.raw:%s"'''
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
                return pool.pool(id, name, protection_domain_id, replicate_size, pool_type, failure_domain_type, device_type, status, action_status, pool_mode, pool_role, self.cluster)
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
                pool_type = result[4]
                failure_domain_type = result[5]
                device_type = result[6]
                status = result[7]
                action_status = result[8]
                pool_mode = result[9]
                pool_role = result[10]
                return pool.pool(id, name, protection_domain_id, replicate_size, pool_type, failure_domain_type, device_type, status, action_status, pool_mode, pool_role, self.cluster)
            if result_status != 'active':
                time.sleep(check_interval)
                i += 1
            if i == 'check_times':
                raise show_pool_failed('循环检查结束，查询pool状态为%s' % result_status)
    def DeletePool(self, name, force, check_times, check_interval):
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        #根据name获取pool的ID
        stdin,stdout,stderr = ssh.exec_command("xms-cli --user %s --password %s pool list | grep %s | awk '{print $2}'"
                                               % (self.admin_user, self.admin_password, name))
        poolid = int(stdout.read().decode()[:-1])
        cmd1 = 'xms-cli --user %s --password %s' % (self.admin_user, self.admin_password)
        cmd2 = pool.pool.delete_pool(self, id=poolid, force=force)
        cmd = cmd1 + ' ' + cmd2
        print('下发删除存储池的命令：\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()
        result_err = stderr.read().decode()
        if result_out == '':
            print('删除存储池失败')
            exit()
        if result_err != '':
            print('删除存储池失败')
            exit()
        for i in range(1, check_times):
            time.sleep(check_interval)
            stdin, stdout, stderr = ssh.exec_command(
                "xms-cli --user %s --password %s pool list | grep %s | awk '{print $16}'"
                % (self.admin_user, self.admin_password, name))
            result = stdout.read().decode()[:-1]
            if result == '':
                print('第%d次检查，间隔%d秒，删除存储池成功' % (i, check_interval))
                break
            if result == 'deleting':
                print('第%d次检查，间隔%d秒，删除存储池状态是%s，继续' % (i, check_interval, result))
                i += 1
            if i == check_times:
                print('第%d次检查，间隔%d秒，删除存储池失败，状态是%s' % (i, check_interval, result))
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
        cmd2 = host.host.add_host(self, public_ip, private_ip, gateway_ip, admin_ip, roles, type, description)
        cmd = cmd1 + cmd2
        print('下发添加服务器的命令', cmd)
        result = self.cmd(cmd)
        if 'error' in result:
            raise add_host_failed('下发添加服务器的命令返回错误')
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
                return host.host(int(id), name, type, roles, public_ips, private_ip, admin_ip, gateway_ips, description, protection_domain_id, 'active', up, self.cluster)
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
                return host.host(id, name, type, roles, public_ips, private_ip, admin_ip, gateway_ips, description, protection_domain_id, status, up, self.cluster)
            if i == check_times:
                raise show_host_failed('循环检查结束，服务器状态为%s' % result_status)
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
        cmd1 = 'xms-cli --user %s --password %s' %(self.admin_user, self.admin_password)
        #由于创建缓存分区的CLI命令下发后，只返回命令下发成功与否，所以不能判断添加缓存分区是否为active
        for i in disk_list:
            cmd2 = partition.partition.create_partition(self, i, num)
            cmd = cmd1 + cmd2
            result = self.cmd(cmd)
            print('下发创建缓存分区的命令\n', cmd)
            print(result)
            if 'Incorrect' in result:
                raise create_partition_failed('创建缓存分区的命令返回错误')
        for j in disk_list:
            for k in range(0, check_times):
                cmd_str = "xms-cli --user %s --password %s partition list --disk %d| awk '{print $2}'| grep -v ID" % (self.admin_user, self.admin_password, j)
                print('下发查看创建的缓存分区的ID\n', cmd_str)
                result = self.cmd(cmd_str)
                print(result)
                if result == None:
                    print('第%d次检查创建缓存分区，返回ID为空，继续检查' % k)
                    k += 1
                    time.sleep(check_interval)
                if result != None:
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
        for i in range(0, len(disk_list)):
            cmd1 = 'xms-cli --user %s --password %s ' %(self.admin_user, self.admin_password)
            cmd2 = osd.osd.create_osd(self, disk_list[i], cache_partition_list[i], read_cache_size, role)
            cmd3 = " | grep id | grep -v host | grep -v pool | grep -v disk | grep -v osd | grep -v partition | awk '{print $4}'"
            cmd = cmd1 + cmd2 + cmd3
            print('下发添加osd并获取osd的id的命令：\n', cmd)
            result = self.cmd(cmd)
        #这下面的改掉，改成不检查状态；当前采用逐个添加并检查状态，之后添加硬盘采用统一添加后再来检查状态的方式，可以节省一大半时间
            if 'error' in result:
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
        result_list.remove('')
        #列表中的元素改成整型，并从小到大排序
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
        #在每个节点上获取指定类型和个数的硬盘，组成整型列表
        for i in range(0, len(host_list)):
            cmd1 = "xms-cli -f '{{range .}}{{println .disk_type}}{{println .id}}{{end}}' --user %s --password %s " % (self.admin_user, self.admin_password)
            cmd2 = '''disk list -q "host.id:%d"| grep -A 1 %s | grep -v %s''' % (host_list[i].id, type, type)
            cmd = cmd1 + cmd2
            out1 = self.cmd(cmd)
            #正则，按换行符\n切割返回的字符串，并把结果转成列表
            out2 = re.split('\n', out1)
            #去掉out2中的重复元素，列表顺序不变
            out2 = sorted(set(out2), key=out2.index)
            try:
                out2.remove('--')
                out2.remove('')
            except:
                pass
            #去掉其中的系统盘，获取前面disk_per_host块盘
            for i in system_disk_id_list:
                try:
                    out2.remove(i)
                except:
                    pass
            for j in range(0, disk_per_host):
                disk_id_list.append(out2[j])
            #disk的id用来创建osd和partition，创建osd和partition只能一个一个disk创建，返回列表比返回字符串要好得多
            #把列表中的元素改成整型，排序后返回
        for i in range(0, len(disk_id_list)):
            for k in disk_id_list:
                disk_id_list.remove(k)
                disk_id_list.append(int(k))
        disk_id_list.sort()
        print('获取到的硬盘ID为：',disk_id_list)
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
        cmd2 = client_group.client_group.create_client_group(type, description, codes, name)
        cmd = cmd1 + cmd2
        print('时间点：\n下发创建客户端组的命令：\n',cmd)
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
                    return client_group.client_group(id, name, type, description, client_num, access_path_num, block_volume_num, result_status, codes, self.cluster)
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
                cluster = self.cluster
                return client_group.client_group(id, name, type, description, client_num, access_path_num, block_volume_num, status, codes, cluster)
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
        cmd2 = access_path.access_path.create_access_path(self, type, name, tname, tsecret, chap, description)
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
                return access_path.access_path(id, name, type, description, protection_domain_id, volume_num, client_group_num, chap, tname, tsecret,
                                               status, action_status, create, self.cluster)

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
        return access_path.access_path(id, name, type, description, protection_domain_id, volume_num, client_group_num,
                                       chap, tname, tsecret, status, action_status, create, self.cluster)
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
        cmd1 = 'xms-cli --timeout=3m --user %s --password %s ' % (self.admin_user, self.admin_password)
        #因为命令中只能跟ID，是一个数，查ID太麻烦了，最好能直接用访问路径对象的形式传入，在关键字里对象.id来获取id，
        #然后远程调用create_mapping_group比较好
        cmd2 = mapping_group.mapping_group.create_mapping_group(self, block_volumes_ids, access_path, client_group)
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
                return mapping_group.mapping_group(id, access_path_id, access_path_name, client_group_id, client_group_name, status, create_time, self.cluster)
            elif result_status != 'active':
                time.sleep(check_interval)
                print('第%d次检查，检查间隔%d秒，创建映射组失败，状态是%s' % (i, check_interval, result_status))
                i += 1
            if i == check_times or result_status == 'error':
                raise create_mappinggroup_failed('循环检查结束，创建%d号映射组失败，状态为%s' % (id, result_status))
    def ShowMappingGroup(self, access_path_name):
        '''
        根据访问路径的名称查看添加进来的映射组，返回映射组对象组成的列表
        :param access_path_name: 访问路径的名称
        :return:
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
                mappinggroup_list.append(mapping_group.mapping_group(id, access_path_id, access_path_name, client_group_id, client_group_name, status, create, self.cluster))
        return mappinggroup_list
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
        # 因为命令中只能跟ID，是一个数，查ID太麻烦了，最好能直接用访问路径对象的形式传入，在关键字里对象.id来获取id，
        # 然后远程调用target比较好
        cmd2 = target.target.create_target(access_path, host)
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
                return target.target(id, host_id,board,port,iqn,access_path_id,status,create,self.cluster)
            elif result_status != 'active':
                time.sleep(check_interval)
                print('第%d次检查，检查间隔%d秒，创建映射组失败，状态是%s' % (i, check_interval, result_status))
                i += 1
            if i == check_times:
                print('第%d次检查，创建映射组失败' % i)
                raise create_target_failed('循环检查结束，给%d号访问路径添加的%d号网关服务器状态为%s' %(access_path,host,result_status))
    def ShowTarget(self,access_path_name):
        '''
        返回指定访问路径上的网关服务器对象
        :return:
        '''
        class show_target_failed(Exception):
            pass
        target_object_list = []
        cmd = '''xms-cli -f '{{range .}}{{println .id}}{{end}}' --user %s --password %s target list -q "access_path.name.raw:%s"''' % (self.admin_user, self.admin_password, access_path_name)
        target_id_list = self.cmd(cmd)
        target_id_list = target_id_list.split('\n')
        for i in range(0,len(target_id_list)):
            for j in target_id_list:
                target_id_list.remove(j)
                target_id_list.append(int(j))
        for k in target_id_list:
            result = self.cmd('''xms-cli -f '{{range .}}{{println .id}}{{println .host.id}}{{println .board}}{{println .port}}{{println .iqn}}{{println .access_path.id}}{{println .status}}{{println .create}}{{end}}' --user %s --password %s target list -q "id.raw:%d"''' %(self.admin_user,self.admin_password,k))
            result = result.split('\n')
            id = int(result[0])
            host_id = int(result[1])
            board = int(result[2])
            port = int(result[3])
            iqn = result[4]
            access_path_id = int(result[5])
            status = result[6]
            create = result[7]
            target_obj = target.target(id, host_id, board, port, iqn, access_path_id, status, create, self.cluster)
            target_object_list.append(target_obj)
        return target_object_list
    def DeleteMappinggroup(self):
        #创建和删除映射组的KW实现都有问题，不好用。目标是传入对象来当参数，当前只能传入已知的ID，
        #这几乎是不能用的。国庆改下
        return 1
    def DeleteTarget(self,id):
        return 1

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
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        cmd = 'xdcadm -L %s -m %s -o %s' %(L,m,o)
        print('下发xdcadm查询命令\n',cmd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err == '':
            return result_out
        if result_err !='':
            raise xdcapi_call_failed
    def check_status(self,cmd,check_entry,relate,expect_value='',check_times=0,check_interval=0):
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
        check_entry_1 = '(?<= %s: )\S*' %check_entry
        #获取字段，返回结果是值组成的列表
        try:
            get_value = re.findall(check_entry_1,result_out)
        except:
            raise check_status_failed('查询字段的值失败')
    def cleanup(self):
        pass
    def close(self):
        self.transport.close()
        del self
# if __name__ == '__main__':
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
    # result = node1.CreatePool(osds='81,82,83,84,85,86,87,88',name='POOL3',pool_type='erasure',check_times=25,check_interval=5)
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

