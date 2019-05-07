# coding=utf-8
# from Testbed import testbed
# from config.version.saneryiwu.VOLUME import volume as volume
# from config.version.saneryiwu.NODE import NODE as NODE

import paramiko
import time
import random
import re
import socket
class pool():
    def __init__(self,id,name,protection_domain_id,replicate_size,type,failure_domain_type,
                 device_type,status,action_status,pool_mode,pool_role):
        self.id = id
        self.name = name
        self.protection_domain_id = protection_domain_id
        self.replicate_size = replicate_size
        self.type = type
        self.failure_domain_type = failure_domain_type
        self.device_type = device_type
        self.status = status
        self.action_status = action_status
        self.pool_mode = pool_mode
        self.pool_role = pool_role

    @staticmethod
    def create_pool(osds, type, size, pool_role, failure_domain_type, pool_name, data_chunk_num, coding_chunk_num):
        '''
        osds，必选，osd的列表，可以通过show osd查看到，例子：1,2,3,4,5,6,7,8
        pool-type 必选，存储池的类型，取值范围（replicated和erasure）二选一，例子：replicated
        size 可选，如果type选副本，则必选，取值范围1-6，例子：3
        pool-role 可选，存储池角色，取值范围（data和index）二选一（默认data）例子：data
        failure-domain-type 可选，故障域范围，取值范围（host和rack和datacenter）三选一，默认host，例子：host
        data-chunk-num  可选，如果type选erasure，则必选，取值范围：正整数
        coding-chunk-num 可选，如果type选erasure，则必选，取值范围：正整数
        '''
        if type == 'replicated':
            cmd = 'pool create --osds %s --pool-type replicated --size %d --pool-role %s --failure-domain-type %s %s' \
                   %(osds,size,pool_role,failure_domain_type,pool_name)
        elif type == 'erasure':
            cmd = 'pool create --osds %s --pool-type erasure --pool-role %s --failure-domain-type %s --data-chunk-num %d --coding-chunk-num %d %s'%(osds,pool_role,failure_domain_type,data_chunk_num,coding_chunk_num,pool_name)
        return cmd

    @staticmethod
    def delete_pool(id, force):
        #id    要删除的POOL的ID
        #force  是否强制删除,取值范围yes|no二选一，默认:no
        if force =='true':
            cmd = 'pool delete --force %d' %id
        elif force == 'false':
            cmd = 'pool delete %d' %id
        return cmd
    # def list_pool(self):
    #     #xms-cli --user admin --password admin pool list
    # def show_pool(self,id):
    #     #xms-cli --user admin --password admin pool show <id>
    # def show_pool(self):
    #
    # def list_pool(self):
    #
    # def reweight_pool(self):
    #
    # def set_pool(self):
    #
    # def add_pool(self):
    #
    # def remove_pool(self):
    #     cmd2 = 'pool reweight '
    def CreateVolume(self, size, name, qos_enabled='false', max_total_iops=1000, max_total_bw=4194304000, max_burst_iops=2000, max_burst_bw=8388608000,format=128,performance_priority=0,check_times=0,check_interval=0):
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
        temporary_node = self.get_available_node()
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = volume.volume.create_volume(self, self.id, size, name, format, performance_priority, qos_enabled, max_total_iops, max_total_bw, max_burst_iops, max_burst_bw)
        cmd = cmd1 + cmd2
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        print('下发创建VOLUME的命令：', cmd)
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd)
        except socket.error as e:
            print('出现socket.error')
        stdout_result = stdout.read().decode()[:-1]
        stderr_result = stderr.read().decode()[:-1]
        if stderr_result != '':
            print('创建VOLUME失败')
            return stderr_result
        else:
            id = int(re.findall('(?<=\| id                   \| )\w*', stdout_result)[0])
        for i in range(0, check_times):
            stdin, stdout, stderr = ssh.exec_command(
                "xms-cli --user %s --password %s block-volume show %d" % (temporary_node[3], temporary_node[4], id))
            stdout_result_status = stdout.read().decode()[:-1]
            result = re.findall('(?<=\| status               \| )\w*', stdout_result_status)[0]
            # 用交互式解释器，实验一把，其实result的值是active\n
            if result == 'active':
                print('第%d次检查创建VOLUME状态，VOLUME的状态是%s,创建VOLUME成功' % (i, result))
                # 需要改成切片的正则表达式或者用其它的方式
                #查看新创建的volume的id
                id = id
                size = re.findall('(?<=\| size                 \| )\w* \w*', stdout_result_status)[0]
                size = size.split(' ')
                size[0] = int(size[0])
                if size[1] == 'GiB':
                    size[1] = 1073741824
                if size[1] == 'MiB':
                    size[1] = 1048576
                if size[1] == 'KiB':
                    size[1] = 1024
                size = size[0]*size[1]
                pool_id = int(re.findall('(?<=\| pool.id              \| )\w*', stdout_result_status)[0])
                pool_name = re.findall('(?<=\| pool.name            \| )\w*', stdout_result_status)[0]
                snapshot_id = re.findall('(?<=\| snapshot.id          \| )\w*', stdout_result_status)[0]
                snapshot_name = re.findall('(?<=\| snapshot.name        \| )\w*', stdout_result_status)[0]
                status = result
                action_status = re.findall('(?<=\| action_status        \| )\w*', stdout_result_status)[0]
                flattened = re.findall('(?<=\| flattened            \| )\w*', stdout_result_status)[0]
                format = re.findall('(?<=\| format               \| )\w*', stdout_result_status)[0]
                description = re.findall('(?<=\| description          \| )\w*', stdout_result_status)[0]
                create = re.findall('(?<=\| create               \| )\w*', stdout_result_status)[0]
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .qos.max_total_iops}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"'''
                                                         % (temporary_node[3], temporary_node[4], name))
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
                sn = stdout.read().decode()[:-1]
                sn = sn.upper()
                performance_priority = performance_priority
                qos_enabled = qos_enabled
                cluster = self.cluster
                return volume.volume(id, name, size, pool_id, pool_name, snapshot_id, snapshot_name, status, action_status,
                                     flattened, format, qos_max_total_iops, qos_max_total_bw, qos_burst_total_iops, qos_burst_total_bw,
                                     description, create, sn, performance_priority, qos_enabled, cluster)
            elif result != 'active':
                print('第%d次检查创建Volume状态，Volume的状态是%s,继续' % (i, result))
                time.sleep(check_interval)
                i += 1
            if i == check_times:
                create_volume_failed('第%d次检查创建Volume状态，创建Volume失败' % check_times)
        try:
            ssh.close()
        except:
            print('pool.py 202关闭ssh连接失败')
    def ShowVolume(self,name,check_times=1,check_interval=1):
        '''

        :param name: 要查询的卷的名称
        :return: 返回循环检查的结果，并作为新对象返回
        '''
        class show_volume_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        for i in range(0, check_times):
            stdin,stdout,stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"'''
                                        % (temporary_node[3], temporary_node[4], name))
            result_status = stdout.read().decode()[:-1]
            if result_status == 'active':
                print('查询卷%s成功' % name)
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .size}}{{println .pool.id}}{{println .pool.name}}{{println .snapshot_id}}{{println .snapshot_name}}{{println .status}}{{println .action_status}}{{println .flattened}}{{println .format}}{{println .description}}{{println .create}}{{println .performance_priority}}{{println .qos_enabled}}{{println .qos.max_total_iops}}{{println .qos.max_total_bw}}{{println .qos.burst_total_iops}}{{println .qos.burst_total_bw}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"'''% (temporary_node[3], temporary_node[4], name))
                out = stdout.read().decode().split('\n')[:-1]

            if result_status != 'active':
                print('第%d次查看卷%s的状态是%s' % (i, name, result_status))
                time.sleep(check_interval)
                i += 1
            if i == check_times:
                raise show_volume_failed('循环检查卷结束，卷%s的卷状态是%s，不正常' % (name, result_status))
        #return self.volumeid = int(out[0])
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
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .sn}}{{end}}' --user %s --password %s block-volume list -q "name.raw:%s"'''% (temporary_node[3], temporary_node[4], name))
                sn = stdout.read().decode()[:-1]
                sn = sn.upper()
                try:
                    qos_max_total_iops = int(out[15])
                    qos_max_total_bw = int(out[16])
                    qos_burst_total_iops = int(out[17])
                    qos_burst_total_bw = int(out[18])
                except:
                    qos_max_total_iops = None
                    qos_max_total_bw = None
                    qos_burst_total_iops = None
                    qos_burst_total_bw = None
                cluster = self.cluster
                return volume.volume(id, name, size, pool_id, pool_name, snapshot_id, snapshot_name, status, action_status, flattened, format, qos_max_total_iops, qos_max_total_bw, qos_burst_total_iops, qos_burst_total_bw, description, create, sn, performance_priority, qos_enabled, cluster)
    def delete(self,check_times=5,check_interval=5):
        '''
        只有pool对象可以删除pool
        :param check_times:
        :param check_interval:
        :return:
        '''
        class delete_pool_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'pool delete %d' % self.id
        cmd = cmd1 + cmd2
        print('下发删除pool的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return result_err + result_out
        # 判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s pool list -q "id:%d"''' \
                  % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
                # 移除对象self
                print('第%d次检查，删除pool成功' % (i + 1))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，删除pool失败，pool状态是%s' % ((i + 1), result_out))
                i += 1
            elif i == check_times:
                raise delete_pool_failed('循环检查结束，删除%d号pool失败' % self.id)
# if __name__ == '__main__':
#     id = 1
#     name = 'POOL1'
#     protection_domain_id = 1
#     replicate_size = 2
#     type = 'replicated'
#     failure_domain_type = 'host'
#     device_type = 'HDD'
#     status = 'active'
#     action_status = 'active'
#     pool_mode = ''
#     pool_role = 'data'

    # POOL1 =  pool(id,name,protection_domain_id,replicate_size,type,failure_domain_type,device_type,status,action_status,pool_mode,pool_role)
    # print(POOL1.id)
    # print(type(POOL1))
    # result = POOL1.CreateVolume(4,5)
    # print('result',result)
