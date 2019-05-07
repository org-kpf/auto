# coding=utf-8
import time
# from Testbed import testbed
# from config.version.saneryiwu.SNAPSHOT import snapshot as snapshot
import paramiko
import random
import re
class volume():
    def __init__(self,id,name,size,pool_id,pool_name,snapshot_id,snapshot_name,status,action_status,flattened,format,
                 qos_max_total_iops,qos_max_total_bw,qos_burst_total_iops,qos_burst_total_bw,description,create,sn,performance_priority,qos_enabled):
        self.id = id
        self.name = name
        self.size = size
        self.pool_id = pool_id
        self.pool_name = pool_name
        self.snapshot_id = snapshot_id
        self.snapshot_name = snapshot_name
        self.status = status
        self.action_status = action_status
        self.flattened = flattened
        self.format = format
        self.qos_max_total_iops = qos_max_total_iops
        self.qos_max_total_bw = qos_max_total_bw
        self.qos_burst_total_iops = qos_burst_total_iops
        self.qos_burst_total_bw = qos_burst_total_bw
        self.description = description
        self.create = create
        self.sn = sn
        self.performance_priority = performance_priority
        self.qos_enabled = qos_enabled
    @staticmethod
    def create_volume(pool, size, name, format, performance_priority, qos_enabled, max_total_iops, max_total_bw, max_burst_iops, max_burst_bw):
        '''

        :param pool: 存储池的ID
        :param size: VOLUME的大小，单位：B,例子1：104857600  例子2：20GB
        :param name: volume的名称
        :param format: 指定VOLUME的类型，取值范围（2|128|129），分别对应V2|V3|V4类型的VOLUME，默认128
        :param performance_priority: 性能优先级，取值范围（0|1），分别是（默认|优先），默认是0
        :param qos_enabled: QoS开关，默认：关闭，例子：yes
        :param max_total_iops: 最大IOPS，取值范围，自然数，默认是0，表示不限制IOPS
        :param max_total_bw: 最大带宽，取值范围，自然数，单位B/s
        :param max_burst_iops: 突发IOPS，突发IOPS要大于等于最大IOPS
        :param max_burst_bw: 突发带宽，取值范围，自然数，单位B/s，突发带宽要大于等于最大带宽
        :return:
        '''
        if qos_enabled == 'false':
            cmd = 'block-volume create --pool=%d --size=%s --format=%s --performance-priority=%d %s' %(pool,size,format,performance_priority,name)
        else:
            cmd = 'block-volume create --pool=%d --size=%s --format=%s --performance-priority=%d --qos-enabled=%s --max-total-iops=%d --max-total-bw=%d --max-burst-iops=%d --max-burst-bw=%d %s' %(pool,size,format,performance_priority,qos_enabled,max_total_iops,max_total_bw,max_burst_iops,max_burst_bw,name)
        return cmd
    def CreateSnapshot(self,name,block_volume,description='',check_times=0,check_interval=0):
        '''
        卷对象创建快照
        :param name: 新建快照的名称，必选
        :param description: 新建快照的描述，可选
        :param check_times: 循环检查新建快照状态是否为active，循环检查次数，可选，默认不检查
        :param check_interval: 循环检查新建快照状态是否为active，循环检查间隔，可选，默认不检查
        :return: 快照对象
        '''
        class create_volume_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = snapshot.snapshot.create_snapshot(self,name,self.id,description)
        cmd = cmd1 + cmd2
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        print('下发创建快照的命令：', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stderr_result = stderr.read().decode()[:-1]
        if stderr_result != '':
            print('创建%d号卷的快照失败' %self.id)
            return stderr_result
        for i in range(0, check_times):
            # 设置检查时间间隔为check_interval秒
            time.sleep(check_interval)
            stdin, stdout, stderr = ssh.exec_command(
                '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s block-snapshot list -q "name:%s"''' % (temporary_node[3],temporary_node[4],name))
            result = stdout.read().decode()[:-1]
            # 用交互式解释器，实验一把，其实result的值是active\n
            if result == 'active':
                print('第%d次检查快照%s状态，快照的状态是%s,创建快照成功' % (i, name,result))
                # 需要改成切片的正则表达式或者用其它的方式
                #查看新创建的volume的id
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .snap_name}}{{println .size}}{{println .allocated_size}}{{println .status}}{{println .volume.id}}{{println .volume.name}}{{end}}' --user %s --password %s block-snapshot list -q "name:%s"'''
                                        % (temporary_node[3],temporary_node[4],name))
                out = stdout.read().decode()[:-1]
                out = out.split('\n')
                id = int(out[0])
                name = out[1]
                snap_name = out[2]
                size = int(out[3])
                allocated_size = int(out[4])
                status = out[5]
                volume_id = int(out[6])
                volume_name = out[7]
                return snapshot.snapshot(id,name,snap_name,size,allocated_size,status,volume_id,volume_name)
            if result != 'active':
                print('第%d次检查创建快照%s状态，快照的状态是%s,继续检查' % (i, name,result))
                time.sleep(check_interval)
                i += 1
            if i == check_times:
                raise create_volume_failed('循环检查结束，创建快照%s失败' %name)

    def delete(self,check_times=8,check_interval=5):
        '''

        :return:
        '''
        class delete_volume_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'block-volume delete %d' % self.id
        cmd = cmd1 + cmd2
        print('下发删除卷的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return result_err + result_out
        # 判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' \
                  % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
                # 移除对象self
                # 移除对象self
                print('第%d次检查，删除卷成功' % (i + 1))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，删除卷失败，卷状态是%s' % ((i + 1), result_out))
                i += 1
            elif i == check_times:
                raise delete_volume_failed('循环检查结束，删除%d号卷失败' % self.id)

    def ShowSnapshot(self,name,check_times=5,check_interval=5):
        '''

        :param name: 要查询的快照的名称
        :return: 返回查到的快照对象
        '''
        class show_snapshot_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        for i in range(0,check_times):
            stdin,stdout,stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s block-snapshot list -q "name:%s"'''
                                        % (temporary_node[3], temporary_node[4], name))
            result_status = stdout.read().decode()[:-1]
            if result_status == 'active':
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .id}}{{println .name}}{{println .snap_name}}{{println .size}}{{println .allocated_size}}{{println .status}}{{println .volume.id}}{{println .volume.name}}{{end}}' --user %s --password %s block-snapshot list -q "name:%s"'''
                                        % (temporary_node[3],temporary_node[4],name))
                out = stdout.read().decode()[:-1]
                out = out.split('\n')
                id = int(out[0])
                name = out[1]
                snap_name = out[2]
                size = int(out[3])
                allocated_size = int(out[4])
                status = out[5]
                volume_id = int(out[6])
                volume_name = out[7]
                return snapshot.snapshot(id, name, snap_name, size, allocated_size, status, volume_id, volume_name)
            if result_status != 'active':
                time.sleep(check_interval)
                print('循环查看快照%s，状态%s不为active，继续检查' %(name,result_status))
                i += 1
            if i == check_times:
                raise show_snapshot_failed('循环检查快照%s结束，快照状态%s不正常' %(name,result_status))

    def set(self,check_times=0,check_interval=0,**kwargs):
        '''
        由volume对象调用，传入参数修改卷对象，循环检查每项修改后的值和传入值是否一致，循环结束才能修改对象特性值
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
        :return: 下发错误，返回命令回显；下发成功，修改对象的字段
        '''
        class set_volume_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s '%(temporary_node[3],temporary_node[4])
        cmd2 = 'block-volume set'
        cmd3 = ''
        cmd4 = ' %d' %self.id
        for i in kwargs:
            if '_' in i:
                m = re.sub('_','-',i)
            else:
                m = i
            if isinstance(kwargs.get(i),int):
                cmd3 = cmd3 + ' --' + m + '=%d' %kwargs.get(i)
            if isinstance(kwargs.get(i),str):
                cmd3 = cmd3 + ' --' + m + '=%s' % kwargs.get(i)
        cmd  = cmd1 + cmd2 + cmd3 + cmd4
        print('下发修改卷的命令\n',cmd)
        stdin,stdout,stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        print(result_out + result_err)
        #命令下发失败，返回回显，不管成功失败都查询一遍，修改卷对象的特性
        if result_out == '' or result_err != '' or 'Incorrect Usage' in result_out:
            return(result_err+result_out)
        #查询修改后的特性是否和传入的参数值一致，name,flattened,qos_enabled，description的值为字符串，API中字段和CLI字段一致，所以放在一组
        for j in list(set(kwargs.keys()).intersection(set(['name', 'flattened', 'qos_enabled', 'description']))):
            for k in range(0,check_times):
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (j, temporary_node[3], temporary_node[4], self.id))
                result = stdout.read().decode()[:-1]
                if result == kwargs.get(j):
                    self.__dict__[j] = kwargs.get(j)
                    break
                if result != kwargs.get(j):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，不同' %(k,j,result,kwargs.get(j)))
                    k += 1
                    time.sleep(check_interval)
                if k == check_times:
                    print(kwargs)
                    raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s,而传入为%s不一致' %(self.id,j,result,kwargs.get(j)))
        # 查询修改后的特性是否和传入的参数值一致，size和performance_priority的值为整型自然数，API中字段和CLI字段一致，所以放在一组
        for l in list(set(kwargs.keys()).intersection(set(['size', 'performance_priority']))):
            for k in range(0,check_times):
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (l, temporary_node[3], temporary_node[4], self.id))
                result = int(stdout.read().decode()[:-1])
                if result == kwargs.get(l):
                    self.__dict__[l] = kwargs.get(l)
                    break
                if result != kwargs.get(l):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，不同' %(k,l,result,kwargs.get(l)))
                    k += 1
                    time.sleep(check_interval)
                if k == check_times:
                    raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s,而传入为%s不一致' %(self.id,l,result,kwargs.get(l)))
        # 查询修改后的特性是否和传入的参数值一致，max_total_iops,max_total_bw,burst_total_iops,burst_total_bw的值为整型自然数，API中字段和CLI字段不一致，所以放在一组
        qos_list = list(set(kwargs.keys()).intersection(set(['max_total_iops','max_total_bw','burst_total_iops','burst_total_bw'])))
        for m in qos_list:
            for k in range(0,check_times):
                stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .qos.%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (m, temporary_node[3], temporary_node[4], self.id))
                result = int(stdout.read().decode()[:-1])
                if result == kwargs.get(m):
                    #在每个m元素前加上qos_
                    n = 'qos_' + m
                    self.__dict__[n] = kwargs.get(m)
                    break
                if result != kwargs.get(m):
                    print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，相同' %(k,m,result,kwargs.get(m)))
                    k += 1
                    time.sleep(check_interval)
                if k == check_times:
                    raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s,而传入为%s不一致' % (self.id, m, result, kwargs.get(m)))

        # for k in range(0,check_times):
        #     for j in kwargs and ['name', 'flattened', 'qos_enabled', 'description']:
        #         stdin,stdout,stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' %(j,temporary_node[3],temporary_node[4],self.id))
        #         result = stdout.read().decode()[:-1]
        #         if result == kwargs.get(j):
        #             print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s，相同' %(k,j,result,kwargs.get(j)))
        #             self.j = kwargs.get(j)
        #         if result != kwargs.get(j):
        #             time.sleep(check_interval)
        #             print('第%d次检查修改卷结果，卷的%s为%s,传入值为%s,不相同，继续检查' % (k, j, result,kwargs.get(j)))
        #             k += 1
        #         if k == check_times:
        #             raise set_volume_failed('循环检查结束，修改%d号卷后的%s为%s和传入不一致' %(self.id,j,result))
        #     for l in kwargs and ['size','performance_priority']:
        #         stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (l, temporary_node[3], temporary_node[4], self.id))
        #         result = int(stdout.read().decode()[:-1])
        #         if result == kwargs.get(l):
        #             self.j = kwargs.get(l)
        #         if result != kwargs.get(l):
        #             time.sleep(check_interval)
        #             print('第%d次检查修改卷结果，卷的%s与设置不符，继续检查' % (k, l))
        #             k += 1
        #         if k == check_times:
        #             raise set_volume_failed('循环检查结束，修改%d号卷后的%s和传入不一致' %(self.id,l))
        #     for m in kwargs and ['max_total_iops','max_total_bw','burst_total_iops','burst_total_bw']:
        #         stdin, stdout, stderr = ssh.exec_command('''xms-cli -f '{{range .}}{{println .qos.%s}}{{end}}' --user %s --password %s block-volume list -q "id:%d"''' % (m, temporary_node[3], temporary_node[4], self.id))
        #         result = int(stdout.read().decode()[:-1])
        #         print('第三个循环，result为\n', result)
        #         if result == kwargs.get(m):
        #             self.m = kwargs.get(m)
        #         if result != kwargs.get(m):
        #             time.sleep(check_interval)
        #             print('第%d次检查修改卷结果，卷的%s为%s与设置不符，继续检查' % (k, m, result))
        #             k += 1
        #         if k == check_times:
        #             raise set_volume_failed('循环检查结束，修改%d号卷后的%s和传入不一致' %(self.id,m))
    def clone_volume(lun_id,snapshot_id,clone_lun_id):
        return 1
    def migrate_volume(source_pool,lun,new_lun):
        return 1
    def roll_back_volume(lun_id,snapshot_id,speed):
        return 1

