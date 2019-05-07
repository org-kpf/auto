import paramiko
from Testbed import testbed
#from config.XebsException import ceph_status_error
import time
import sys
sys.path.append('..')

class LINUXCLIENT(object):

    def __init__(self,ip,business_ip,port,user,passwd):
        self.ip = testbed.host_ip
        self.business_ip = testbed.host_business_ip
        self.port = port
        self.user = testbed.host_user
        self.passwd = testbed.host_password
        self.transport = None
    def connect(self):
        self.transport = paramiko.Transport((self.ip,self.port))
        self.transport.connect(username=self.user,password=self.passwd)
    def hot_add(self):
        #比对WWN
        return self.volume
    def start_fio_IO(self,numjobs,rw,bssplit,ioengine,name,randrepeat,runtime,size,write_bw_log,filename,iodepth):
        ssh = paramiko.SSHClient()
        ssh._transport = self.transport
        return 1
    def stop_fio_IO(self):
        return 1
    def start_vdbench_io(self):
        return 1
    def stop_vdbench_io(self):
        return 1

