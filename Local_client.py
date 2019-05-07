#!/usr/bin/python2.7

# -*- coding: utf-8 -*-
import paramiko
import os
#from Testbed import testbed
#from config.XebsException import ceph_status_error
import time
import sys
import ConfigParser
sys.path.append('..')
reload(sys)
sys.setdefaultencoding("utf-8")
class Local_client:

    # def __init__(self, ip, port, user, password):
    #     self.ip = ip
    #     self.user = user
    #     self.port = port
    #     self.password = password
    def local_client_connect(self, ip, user, password, port=22):
        print('Local客户端%s，端口%s，用户名%s，密码%s' % (ip, port, user, password))
        self.ip = ip
        self.user = user
        self.password = password
        self.transport = paramiko.Transport(ip, port)
        self.transport.connect(username=user, password=password)
    def cmd(self,cmd):
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        stdin,stdout,stderr = ssh.exec_command(cmd)
        stdin.write('y\n')
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return (result_err + result_out)
        else:
            return result_out
    def put(self,local_path, remote_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(local_path, remote_path)
    def get(self,remote_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.get(remote_path, local_path)
    def ScanVolume(self, volume_sn_list):
        '''
        传入lun的SN组成的列表，返回客户端看到的盘符列表
        :param volume_sn_list: 传入的列表，每个元素是字符串，内容是卷的sn，大写的字符串
        :return: 传入卷的sn，返回客户端查看到的所有盘符，以列表的形式
        '''
        disk_list = []
        #卷如果是重新加入映射组，第一时间执行扫卷关键字，查不出来volume_file，这时就重试3次，每次3秒
        for i in range(0, 3):
            volume_file = self.cmd("lvmdiskscan | awk '{print $1}'| grep '^/dev.*[^0-9]$'")
            volume_file = volume_file.split('\n')
            if len(volume_file) < len(volume_sn_list):
                time.sleep(3)
            else:
                break
        if len(volume_file) < len(volume_sn_list):
            raise scan_volume_failed('客户端发现的盘符是', volume_file, '\n少于传入的sn列表', volume_sn_list)
        print('volume_file', volume_file)
        for i in volume_file:
            out = self.cmd("smartctl -a %s | grep Serial | awk '{print $3}'" % i)
            if out in volume_sn_list:
                print('客户端扫卷找到%s对应的盘符' % out)
                disk_list.append(i)
            else:
                # out = out.lower()，返回大写，但API有时返回小写，有时返回大写
                print('客户端扫卷没有找到%s对应的盘符' % out)
                pass
        return disk_list
    def MakeFilesystem(self, format, lun):
        '''

        :param format: 创建文件系统的格式
        :param lun: 卷的盘符
        :return:
        '''
        class MakeFilesystem_failed(Exception):
            pass
        if format in ['ext3', 'ext4']:
            cmd = 'mkfs -t %s %s' % (format, lun)
            print(cmd)
            result = self.cmd(cmd)
            print(result)
            #已经创建文件系统的卷，再次创建文件系统时有err
            if 'Warning' in result:
                raise MakeFilesystem_failed('执行mkfs给卷%s创建文件系统失败' % lun)
            if 'No such file or directory' in result:
                raise MakeFilesystem_failed('执行mkfs给卷%s创建文件系统失败,请检查盘符是否正确' % lun)
            if result[-5:-1] == 'done':
                print('卷%s创建文件系统成功' % lun)
            else:
                print('执行mkfs给卷%s创建文件系统失败，脚本结束' % lun)
                raise MakeFilesystem_failed('执行mkfs给卷%s创建文件系统失败' % lun)
        if format == 'xfs':
            cmd = 'mkfs.xfs %s' % lun
            print(cmd)
            result = self.cmd(cmd)
            print(result)
            if 'Warning' in result:
                raise MakeFilesystem_failed('执行mkfs给卷%s创建文件系统失败' % lun)
            if 'No such file or directory' in result:
                raise MakeFilesystem_failed('执行mkfs给卷%s创建文件系统失败,请检查盘符是否正确' % lun)
            if 'naming   =version 2' in result:
                print('卷%s创建文件系统成功' % lun)
            else:
                print('执行mkfs给卷%s创建文件系统失败，脚本结束' % lun)
                raise MakeFilesystem_failed('执行mkfs给卷%s创建文件系统失败' % lun)
    def mount(self, lun, directory):
        '''

        :param lun: 客户端看到的卷的盘符或者分区
        :param directory: 挂载目录的全路径，例子/mnt/test1
        :return:挂载成功，返回空；挂载失败，返回错误的回显
        '''
        class mount_failed(Exception):
            pass
        cmd = 'mount %s %s' % (lun, directory)
        print('客户端下发挂载文件系统的命令：\n%s' % cmd)
        result = self.cmd(cmd)
        print(result)
        if result != '':
            raise mount_failed('挂载%s上的文件系统失败' % lun)
        else:
            print('%s目录挂载%s上的文件系统成功' % (directory, lun))
    def umount(self, directory):
        '''

        :param directory: 要卸载的目录的全路径，例子/mnt/test1
        :return:
        '''
        class umount_failed(Exception):
            pass
        cmd = 'umount %s' % directory
        print('%s客户端卸载%s目录' % (self.ip, directory))
        result = self.cmd(cmd)
        if result != '':
            raise umount_failed('%s客户端卸载%s目录失败' % (self.ip, directory))
        else:
            pass
    #def StartFio(self,volume_list,rw,bssplit,ioengine,name,randrepeat,runtime,size,write_bw_log,filename,iodepth):
    def StartFio(self,volume_list,**kwargs):
        '''
        volume_list
        必选，需要下业务的volume盘符/目录/文件，要把LUN对象转化成盘符传递给filename，取值范围：列表的每一个元素都是volume对象
        rw
        业务模型，每次下业务，所有lun上的业务模型都是一样的；想要不同的业务模型，需要多起几个fio进程
        取值范围：randrw,randwrite,randread,randtrim,write,read,trim,trimwrite,rw,共9种，fio默认：read；例子：rw=write:8k
        每次写之后将会跳过8K。它将顺序的IO转化为带有洞的顺序IO
        rwmixread
        混合读写中读的比例，取值范围：自然数[0,100]，默认：50
        bs
        读写块的大小，单位B，取值范围[512，+∞],可以是数字+k/K，或者数字+m/M，fio默认：4k
        #如果是读写混合，可以写成bs=5k,8k  中间用逗号分隔，表示读IO大小5K，写IO大小8K，如果有一个没有，则默认4K
        bssplit
        指定混合大小的读写IO和各自的比例；例子：32k/30:64k/30:1m/40
        size
        读写区域的长度，和offset配合，单位B或者%，可以是数字+K,数字+M，数字+G的形式，
        也可以是20%，30%的形式，表示使用给定设备的20%，30%，默认：全lun
        offset
        和size配合，单位同size，size=20G,offset=10G,则表示读写块设备的[10GB,30GB]的区域，默认：0
        ioengine
        定义工具向设备发起IO的方式，默认，sync,取值范围：
        sync（基本的read,write,lseek用来定位），psync（基本的pread,pwrite）
        vsync（基本的readv,writev），libaio（linux专有的异步IO，linux只支持非buffered IO的队列行为）
        posixaio（glibc posix异步IO），solarisaio（solaris独有的异步IO），windowsaio（windows独有的异步IO）
        mmap（文件通过内存映射到用户空间），splice（使用splice和vmsplice在用户空间和内核之间传输数据）
        syslet-rw（使用syslet系统调用来构造普通的read/write异步IO），调试参数时一直报失败！
        sg SCSI generic sg v3 io.可以是使用SG_IO ioctl来同步，或是目标是一个sg字符设备，我们使用read和write执行异步IO，sg只能用来测块设备，不能测文件
        null（不传输任何数据，只是伪装成这样。用于训练使用fio，或是基本debug/test目的）
        net（根据给定的host:port通过网络传输数据。根据具体的协议，hostname，port，listen，filename这些选项将被用来说明建立哪种连接，哪种协议）
        netsplice（像net，但是使用splic/vmsplice来映射数据和发送/接收数据）
        cpuio（不传输任何数据，但是要根据cpuload=和cpucycle=选项占用CPU周期，比如cpuload=85,job不做任何实际的IO，但要占用85%的CPU周期，在SMP机器上,
        使用numjobs=<no_of_cpu>来后去需要的CPU，因为cpuload仅会载入单个CPU，然后占用需要的比例，只带cpuload可以下发，带cpucycle下发不了
        guasi 一般用于异步IO的用户空间异步系统调用接口；没下发成功过
        rdma支持RDMA内存予以（RDMA_WRITE/RDMA_READ）和通道注意（Send/Recv）用于InfiniBand，RoCE和iWARP协议；每下发成功过
        external 指明要调用一个外部的IO引擎（二进制文件）例子：ioengine=external:/tmp/foo.o将载入/tmp下的foo.o这个IO引擎
        iodepth
        如果IO引擎是异步的，这个指定我们需要保持的队列深度，取值范围，自然数，fio默认：1
        iodepth大于1不会影响同步IO引擎（除非verify_async这个选项被设置）。
        even async engines may impose OS restrictions causing the desired depth not to be achieved.
        这会在Linux使用libaio并且设置direct=1的时候发生，因为buffered io在OS中不是异步的。
        在外部通过类似于iostat这些工具来观察队列深度来保证这个IO队列深度是我们想要的。这个可以参考褚霸的博客http://blog.yufeng.info/archives/2104
        direct
        取值范围（0|1），1表示非buffer的IO，0表示buffer的IO，ZFS和Solaris和windows的同步IO引擎不支持direct io
        buffered
        取值范围（0|1），意义和direct相反
        nrfiles
        取值范围：自然数，用于这个job的文件数据，默认为1
        openfiles
        取值范围自然数，在同一时间可以同时打开的文件数目，默认同nrfiles相等，可以设置小一些，来限制同时打开的文件数目
        numjobs
        取值范围自然数，给每个job创建指定数量的副本线程，可能是创建大量的线程/进程来执行同一件事。我们将这样一系列的job，看作一个特定的group
        fio默认值：1
        rate
        限制每个job的带宽，单位B，取值范围：自然数，也可以带单位，例子：rate=500m，限制job总带宽为500MBps,rate=100m,200m  中间是逗号，限制读带宽为100MBps，限制写带宽为200MBps
        ratemin
        限制每个job的最小带宽，单位取值用法同rate
        time_based
        没有取值，当有这个参数时，表示fio运行以时间为准，如果没有time_based，fio最多把块设备覆盖一遍就会结束（除非指定了很大的io_limit）
        runtime
        前提：有time_based存在，取值范围：自然数，单位：秒，FIO很难指定单个job的运行时间，用来指定fio运行的总时间比较好
        ramp_time
        前提：有time_based存在，取值范围：自然数，单位：秒，性能测试中用到的预热时间
        设定在记录任何性能信息之前要运行特定负载的时间。这个用来等性能稳定后，再记录日志结果，因此可以减少生成稳定的结果需要的运行时间
        io_limit
        当没有time_based的时候，来控制下发的业务量，单位B，取值范围：自然数，可以是数字+k/m/g/t，例子：io_limit=100t
        用io_limit可以实现对块设备的覆盖写
        loops
        重复运行某个job的次数，取值范围：自然数，默认：1，例子：loops=5
        verify
        写一个文件是，每次执行完一个job，fio可以校验文件内容，允许的校验算法有（取值范围）：
        md5，crc64，crc32c，crc32c-intel，crc32，crc16，crc7，sha512，sha256，sha1，meta，null，例子：verify=md5
        do_verify
        前提：verify指定了校验的算法，写完后，执行一个校验的阶段，取值范围：（0|1），默认：1，例子：do_verify=1

        '''
        class StartFio_failed(Exception):
            pass
        config = ConfigParser.ConfigParser(allow_no_value=True)
        config.add_section('global')
        for i in kwargs:
            config.set('global', i, kwargs.get(i))
        for i in range(0, len(volume_list)):
            a = 'job%d' % (i + 1)
            config.add_section(a)
            config.set(a, 'filename', volume_list[i])
        file_name = str(int(time.time()))
        with open(file_name, 'wt') as configfile:
            config.write(configfile)
        if os.path.exists(file_name):
            localpath = os.getcwd() + '\\' + file_name
            serverpath = '/home/tools/fio/%s' % file_name
            self.put(localpath, serverpath)
            self.cmd("sed -i 's/ = /=/g' %s" %serverpath)
            start_fio = 'fio %s' % serverpath
            result = self.cmd(start_fio)
            print(result)
            os.remove(file_name)
            return result
        else:
            StartFio_failed('StartFio_failed')
    def stop_fio_IO(self):
        return 1
    def start_vdbench_io(self):
        return 1
    def stop_vdbench_io(self):
        return 1
    def backup_volume(self):
        return 1
    def compare_data_consistent(file1,file2):

        return 1
# if __name__ == "__main__":
#     local_client = Local_client(ip='10.252.3.240',port=22, user='root',password='redhat')
    # local_client1 = local_client(ip=testbed.cluster2_admin_ip[0], port=22, user=testbed.cluster2_node_user, password=testbed.cluster2_node_password)
    # local_client_connect(ip='10.252.3.240',port=22, user='root',password='redhat')
    # local_client1.connect()
    # local_client1.StartFio(['/mnt/test1/file1'],rw='rw',thread = None,size='1GB',group_reporting=None,offset='0')
    # pass

