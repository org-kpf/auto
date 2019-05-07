# coding=utf-8
import paramiko
import os
import ConfigParser
#from config.XebsException import ceph_status_error
import time
import sys
import re
import wmi
sys.path.append('..')




class linux_client:

    # def __init__(self, ip, business_ip, user, password, port=22):
    #     self.ip = ip
    #     self.business_ip = business_ip
    #     self.port = port
    #     self.user = user
    #     self.password = password

    # execute cmd
    def cmd(self, cmd):
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdin.write('y\n')
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return (result_err + result_out)
        else:
            return result_out

    #connect client
    def linux_client_connect(self, ip, user, password, port=22):
        print('连接linux客户端%s，端口%s，用户名%s，密码%s' % (ip, port, user, password))
        self.ip = ip
        self.user = user
        self.password = password
        self.port = port
        self.transport = paramiko.Transport(ip, port)
        self.transport.connect(username=user, password=password)
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)

    def win_client_connect(self, ipaddress, username, password):
        try:
            print "conn %s" %ipaddress
            conn = wmi.WMI(computer=ipaddress, user=username, password=password)
            print conn
            print "conn seccessed"
        except wmi.x_wmi:
            print "conn failed"

    #生成vdbench 配置文件
    def create_vdbench_param(self,ips ,username ,password ,vdbench_home ,threads ,size,wd ,rd,port=22):
        self.ips = ips
        self.username = username
        self.password = password
        self.port = port
        self.vdbench_home = vdbench_home
        self.threads = threads
        self.wd = wd
        self.rd = rd
        self.size = size
        cont = []
        hds = []
        sd_num = 1
        ipl = ips.split(" ")
        hd = "hd=default,vdbench={0},user=root,shell=ssh\n".format(vdbench_home)
        cont.append(hd)
        for host in ipl:
            hd = "".join(host)
            system = ("hd=hd{0},system={1}\n").format(host.split('.')[-1],host.strip('\n'))
            cont.append(system)
            hds.append(hd)

        for hostname in ipl:
            hd = hostname.split('.')[-1]
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(hostname,port,username,password)
            stdin,stdout,sterr = s.exec_command("multipath -F;multipath -v2 >/dev/null;ls -l /dev/mapper/mpath*|awk -F' '  '{print $9}'")
            luns = stdout.readlines()
            for lun in luns:
                sd = "sd=sd{0},hd=hd{1},lun={2},threads={3},size={4},openflags=o_direct\n".format(sd_num,hd.strip('\n'),lun.strip('\n'),threads.strip('\n'),size)
                cont.append(sd)
                sd_num = sd_num + 1
            s.close()
        cont.append(wd)
        cont.append(rd)

        with open(r"vdbench_param","w+") as f:
            for line in cont:
                f.write(line)
        vdbench_param = "vdbench script path:"+os.getcwd()+r"\vdbench_param"
        print vdbench_param
        return vdbench_param

    #创建vdbench_param file
    def create_vdbench_param_file(self,ips,username,password,vdbench_home,depth,width,files,size,fwd,frd,port=22):
        self.ips = ips
        self.username = username
        self.password = password
        self.port = port
        self.vdbench_home = vdbench_home
        self.depth = depth
        self.width = width
        self.files = files
        self.size = size
        self.fwd = fwd
        self.rd = frd
        self.port = port
        cont = []
        hds = []
        fsd_num = 1
        hdss = 1
        ipl = ips.split(" ")
        hd = "hd=default,vdbench={0},user=root,shell=ssh\n".format(vdbench_home)
        cont.append(hd)
        for host in ipl:
            hd = "".join(host)
            system = ("hd=hd{0},system={1}\n").format(hdss,host.strip("\n"))
            cont.append(system)
            hds.append(hd)

        for hostname in ipl:
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            s.connect(hostname,port,username,password)
            stdin,stdout,stderr = s.exec_command("ls -lr  /mnt/ |grep -v total |awk -F' ' '{print $NF}' ")
            dirs = stdout.readlines()
            for dir in dirs:
                fsd = "fsd=fsd{0},anchor=/mnt/{1},depth={2},width={3},files={4},size={5}\n".format(fsd_num,dir.strip('\n'),depth.strip('\n'),width.strip('\n'),files.strip('\n'),size)
                cont.append(fsd)
                fsd_num = fsd_num + 1
            s.close()
        cont.append(fwd)
        cont.append(frd)

        with open(r"vdbench_param_file","w") as file:
            for line in cont:
                file.write(line)

        vdbench_param_file = "vdbench_param_file:"+os.getcwd()+r"\vdbench_param_file"
        print vdbench_param_file
        return vdbench_param_file

    #上传vdbench_parm 到客户端
    def put_vdbench_param(self,ip,user,password,filename,port=22):
        self.ip = ip
        self.user = user
        self.password = password
        self.filename = filename
        self.port = 22
        localpath = os.getcwd() + '\\' + filename
        serverpath = "/home/%s" % (filename)
        self.transport = paramiko.Transport(ip,port)
        self.transport.connect(username=user,password=password)
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.put(localpath, serverpath)


    #启动vdbench
    def start_vdbench(self,ip,user,password,vdbench_home,filename,port=22):
        #print vdbench_home
        class start_vdbench(Exception):
            pass

        print('连接linux客户端%s，端口%s，用户名%s，密码%s' % (ip, port, user, password))
        self.ip = ip
        self.user = user
        self.password = password
        self.port = port
        self.filename = filename
        self.transport = paramiko.Transport(ip, port)
        self.transport.connect(username=user, password=password)
        self.transport = paramiko.Transport(self.ip, self.port)
        self.transport.connect(username=self.user, password=self.password)
        cmd1 = vdbench_home
        cmd2 = "vdbench -v -f /home/%s  -o  /home/output/  >/dev/null 2>&1 &" %(filename)
        cmd ="nohup " + cmd1 + cmd2
        print cmd
        result_status = self.cmd(cmd)
        print result_status
        time.sleep(20)
        cmdexe = "ps axu |grep -v grep|grep vdbench"
        result_status_java = self.cmd(cmdexe)
        #print result_status_java
        if "vdbench" not in result_status_java:
            cmdlog = "cat /home/output/logfile.html"
            log = self.cmd(cmdlog)
            raise  start_vdbench("start vdbench fail %s" %log)
        else:
            return result_status_java


    #get vdbench result
    def get_vdbench_result(self, vpath):
        class check_result(Exception):
            pass
        result = "ERROR"
        recmd = ("cat   %serrorlog.html |grep 'Data Validation Key miscompare'") %(vpath)
        print recmd
        res = self.cmd(recmd)
        print res
        if  'Key miscompare' in res:
            result = "EEEOR"
            raise check_result("Data Validation Key miscompare")
        else:
            result = "CORRECT"
        return result

    #cifs 挂载
    def cifs_mount(self,ip,user,password,cifs_share,share_mount,username,userpassword,cifs_vers,port=22):
        class cifs_mount_fail(Exception):
            pass
        self.ip = ip
        self.user = user
        self.password = password
        self.username = username
        self.userpassword = userpassword
        self.port = port
        self.password = cifs_vers
        self.transport = paramiko.Transport(ip,port)
        self.transport.connect(username=user,password=password)
        cmd = "mount -t cifs " + cifs_share + " " + share_mount + " -o username=%s -o password=%s -o vers=%s" %(username,userpassword,cifs_vers)
        print cmd
        result_status = self.cmd(cmd)
        print result_status

        if result_status =="":
            return result_status
        else:
            raise  cifs_mount_fail("mount fail: %s" % result_status)

    #NFS 挂载
    def nfs_mount(self,ip,user,password,nfs_share,share_mount,vers,mode,port=22):

        class nfs_mount_fail(Exception):
            pass
        self.ip = ip
        self.user = user
        self.password = password
        self.nfs_share = nfs_share
        self.share_mount = share_mount
        self.vers = vers
        self.mode = mode
        self.port = port
        self.transport = paramiko.Transport(ip,port)
        self.transport.connect(username=user,password=password)
        cmd = "mount -t nfs "+ nfs_share + " " + share_mount + " -o  vers=%s  -o %s"  %(vers,mode)
        print cmd
        result_status = self.cmd(cmd)
        if result_status =="":
            return result_status
        else:
            raise nfs_mount_fail("mount fail: %s"  %result_status)


    def get(self, server_path, local_path):
        sftp = paramiko.SFTPClient.from_transport(self.transport)
        sftp.get(server_path, local_path)

    def IscsiLogin(self,gate_way_ip):
        '''
        :param gate_way_ip: 节点的gateway_ip
        :return: 如果连接成功，则pass，否则，抛异常
        '''
        class iscsi_login_failed(Exception):
            pass
        cmd = 'iscsiadm -m discovery -t st -p %s' % gate_way_ip
        print('客户端下发发现Target命令：\n%s' % cmd)
        out = self.cmd(cmd)
        if 'iscsiadm: No portals found' in out:
            print('iscsiadm: No portals found')
            raise iscsi_login_failed('没有发现门户，请检查网络是否正确')
        out1 = out.split(' ')
        ip_bak = out1[0][:-2]
        t_iqn = out1[1]
        cmd1 = 'iscsiadm -m node -T %s -p %s -l' % (t_iqn, ip_bak)
        print('客户端下发连接Target命令：\n%s' % cmd1)
        result = self.cmd(cmd1)
        if result[-11:-1] == 'successful':
            print('客户端%s成功连接节点IP%s' % (self.ip, gate_way_ip))
        else:
            raise iscsi_login_failed('客户端%s连接节点IP%s失败' % (self.ip, gate_way_ip))

    def IscsiLogout(self,gate_way_ip):
        '''
        由于当前一条访问路径只出一个IQN，而一个客户端可以加入多条AP，可能出现多个节点前端IP对应1个IQN的情况
        :param gate_way_ip: 已连接的iSCSI连接中，节点的gate_way_ip
        :return:
        '''
        class iscsi_logout_failed(Exception):
            pass
        #查看已有的iSCSI连接,获取sid
        sid = self.cmd("iscsiadm -m session -P 1 | grep -A 10 %s | grep SID | awk '{print $2}'" % gate_way_ip)
        #获取target_iqn
        tar_iqn = self.cmd("iscsiadm -m session -r %s -o new | grep Logging | awk '{print $7}'" % sid)
        target_iqn = tar_iqn[:-1]
        result = self.cmd('iscsiadm -m node -T %s -p %s:3260 --logout' % (target_iqn, gate_way_ip))
        result = result.split('\n')

    def Back(self, lun, file):
        '''

        :param lun: 卷的盘符，可以通过ScanVolume关键字获得列表，列表元素作为卷的盘符
        :param file: 备份的目的文件的全路径，例子：/home/xsky.bin
        :return: 备份失败，抛异常，备份成功，pass
        '''
        class back_volume_failed(Exception):
            pass
        cmd = 'dd if=%s of=%s' % (lun, file)
        result = self.cmd(cmd)
        if result != '':
            print(result)
            raise back_volume_failed('备份卷%s过程中出现错误' % lun)
        volume_size = self.cmd('du -sh %s' % lun)
        file_size = self.cmd('du -sh %s' % file)
        if volume_size != file_size:
            raise back_volume_failed('备份结束，卷%s的容量和备份文件%s的容量不一致' % (lun, file))
        else:
            pass
    def Diff(self, lun, file):
        '''
        doradoV3可以在连接客户端的情况下回滚，9月后的EBS都不行，这个关键字实际用起来麻烦
        :param lun: 要比较的卷的盘符
        :param file: 要比较的备份文件，全路径，例子：/home/test/backup/beifen1
        :return: 如果不一致，抛异常，如果一致，pass
        '''
        class diff_volume_file(Exception):
            pass
        result = self.cmd('diff %s %s' % (lun, file))
        if result != '':
            print(result)
            raise diff_volume_file('比较卷%s和备份文件%s不一致' % (lun, file))
        else:
            pass
        #删除备份文件
        result2 = self.cmd('rm -rf %s' % file)
        if result2 != '':
            raise diff_volume_file('卷%s和备份文件%s校验一致，但是备份文件%s删除失败' % (lun, file, file))
        else:
            pass

    def ScanVolume(self, volume_sn_list):
        '''
        扫卷，把集群映射过来的卷扫出来，返回客户端看到的卷的盘符
        :return: 列表，列表元素为字符串，如右'/dev/sdx'
        '''
        class scan_volume_failed(Exception):
            pass
        disk_list = []
        #卷如果是重新加入映射组，第一时间执行扫卷关键字，查不出来volume_file，这时我们就重试3次，每次3秒
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
                print('客户端扫卷没有找到%s对应的盘符' % i)
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
        :param lun: 挂载文件系统基于的卷或者分区
        :param director: 目录
        :return:
        '''
        class mount_failed(Exception):
            pass
        cmd = 'mount %s %s' % (lun, directory)
        print('客户端下发挂载文件系统的命令：\n', cmd)
        result = self.cmd(cmd)
        if result != '':
            raise mount_failed('挂载%s上的文件系统失败' % lun)
        else:
            print('%s目录挂载%s上的文件系统成功' % (directory, lun))
    def umount(self,directory):
        '''
        :param director: 要卸载的目录的全路径
        :return:
        '''
        class umount_failed(Exception):
            pass
        cmd = 'umount %s' % directory
        print('%s客户端卸载%s目录' % (self.ip, directory))
        result = self.cmd(cmd)
        #有时下发umount会返回“umount: /mnt/test1: target is busy.”，关键字是强制删呢，还是报错呢？
        if result != '':
            raise umount_failed('%s客户端卸载%s目录失败' % (self.ip, directory))
        else:
            pass
    def StartFio(self, volume_list, **kwargs):
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
        前提：有time_based存在，取值范围：自然数，单位：秒，很难指定单个job的运行时间，用来指定fio运行的总时间比较好
        ramp_time
        前提：有time_based存在，取值范围：自然数，单位：秒，性能测试中用到的预热时间
        设定在记录任何性能信息之前要运行特定负载的时间。这个用来等性能稳定后，再记录日志结果，因此可以减少生成稳定的结果需要的运行时间
        io_limit
        当没有time_based的时候，来控制下发的业务量，单位B，取值范围：自然数，可以是数字+k/m/g/t，例子：io_limit=100t
        用io_limit可以实现对块设备的覆盖写
        loops
        重复运行某个job的次数，取值范围：自然数，默认：1，例子：loops=5
        verify
        写一个文件时，每次执行完一个job，fio可以校验文件内容，允许的校验算法有（取值范围）：
        md5，crc64，crc32c，crc32c-intel，crc32，crc16，crc7，sha512，sha256，sha1，meta，null，例子：verify=md5
        do_verify
        前提：verify指定了校验的算法，写完后，执行一个校验的阶段，取值范围：（0|1），默认：1，例子：do_verify=1
        continue_on_error
        当出现某种错误时，工具继续运行。取值范围：（none|read|write|io|verify|all|0|1）8选一
        none——只要出现一个错误，工具就退出
        read——只有出现read错误时，才继续
        write——只有出现write错误时，才继续
        io——只有出现IO错误，才继续
        verify——只有出现verify错误时，才继续
        all——出现所有IO错误或者verify错误，都继续
        0——同none
        1——同all
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
            self.cmd("sed -i 's/ = /=/g' %s" % serverpath)
            start_fio = 'fio %s' % serverpath
            result = self.cmd(start_fio)
            print(result)
            os.remove(file_name)
            return result
        else:
            StartFio_failed('StartFio_failed')

    def StopFio(self):
        return 1
    def start_vdbench_io(self):
        return 1
    def stop_vdbench_io(self):
        return 1

if __name__ == '__main__':
    # linux_client_1 = linuxclient(testbed.host_ip, testbed.host_business_ip, user=testbed.host_user, password=testbed.host_password)
    #linux_client_1.connect()
    test = linux_client()
    Linux_ip="10.0.11.126"
    username="root"
    password="redhat"
    #localpath = r"‪D:\aotu\vdbench_parm"
    #filename="vdbench_parm"
    #localpath = os.getcwd()+'\\'+filename
    #print localpath
    remotepath = "/root/vdbench/vdbench"
    test.start_vdbench(Linux_ip, username, password,remotepath)

    # linux_client_1.START_FIO_IO(['/dev/sdb'], rw='write', ioengine='libaio', thread=None, bs='1M', size='10GB', group_reporting=None, offset=0, iodepth=32)
    #linux_client_1.IscsiLogin('10.252.2.240')
    # test1 = linux_client_1.cmd('df')
    # print(test1)
    # file_name = '1548238283'
    # localpath = os.getcwd() + '\\' + file_name
    # serverpath = '/home/tools/fio/%s' % file_name
    # linux_client_1.put(server_path=serverpath, local_path=localpath)
    #win_client_connect(ipaddress="10.0.11.129", user="administrator", password="xsky@2018")
