#coding=utf-8
import time
import paramiko

class nodeFault():
    def __init__(self):
        pass

    # 1.
    # 查看开关机状态：
    # ipmitool –H(BMC的管理IP地址) –I  lanplus –U(BMC登录用户名) –P(BMC 登录用户名的密码) power  status
    # 2.
    # 开机：
    # ipmitool –H(BMC的管理IP地址) –I lanplus –U(BMC登录用户名) –P(BMC 登录用户名的密码) power  on
    # 3.
    # 关机：
    # ipmitool –H(BMC的管理IP地址) –I lanplus –U(BMC登录用户名) –P(BMC 登录用户名的密码) power off
    # 4.
    # 重启：
    # ipmitool –H(BMC的管理IP地址) –I lanplus –U(BMC登录用户名) –P(BMC 登录用户名的密码) power reset


    @staticmethod
    def reboot():
        #reboot是重新启动，shutdown -r now是立即停止然后重新启动
        #shutdown命令可以安全地关闭或重启Linux系统，它在系统关闭之前给系统上的所有登录用户提示一条警告信息
        #reboot命令重启动系统时是删除所有的进程，而不是平稳地终止它们。因此，
        # 使用reboot命令可以快速地关闭系统，但如果还有其它用户在该系统上工作时，就会引起数据的丢失
        cmd = "reboot"
        return cmd

    #重启
    @staticmethod
    def reset(bmcip,bmcuser,bmcpassword):
        cmd =  "ipmitool -I lanplus -H %s -U %s -P %s  power reset" %(bmcip,bmcuser,bmcpassword)
        return cmd
    #关机
    @staticmethod
    def powerdown(bmcip,bmcuser,bmcpassword):
        cmd = "ipmitool -I lanplus -H %s -U %s -P %s  power off" %(bmcip,bmcuser,bmcpassword)
        return cmd

    #开机
    @staticmethod
    def poweron(bmcip,bmcuser,bmcpassword):
        cmd = "ipmitool -I lanplus -H %s -U %s -P %s  power on" %(bmcip,bmcuser,bmcpassword)
        return cmd


# if  __name__ == '__main__':
#     test = short_Powerdown()
#     print test

