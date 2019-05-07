# coding=utf-8
import paramiko
import time
import random
# from Testbed import testbed
class target():
    def __init__(self,id,host_id,board,port,iqn,access_path_id,status,create):
        self.id = id
        self.host_id = host_id
        self.board = board
        self.port = port
        self.iqn = iqn
        self.access_path_id = access_path_id
        self.status = status
        self.create = create
    @staticmethod
    def create_target(access_path, host):
        '''
        :param access_path: 访问路径ID
        :param host: 服务器ID，就是选哪个服务器来做网关服务器
        :return:
        '''
        cmd = 'target create --access-path=%d --host=%d' % (access_path, host)
        return cmd
    def delete(self, check_times=5, check_interval=5):
        '''
        只能由网关服务器对象调用删除的方法
        :return:
        '''
        class delete_target_failed(Exception):
            pass
        temporary_node = self.get_available_node()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=temporary_node[0], username=temporary_node[1], password=temporary_node[2])
        cmd1 = 'xms-cli --user %s --password %s ' % (temporary_node[3], temporary_node[4])
        cmd2 = 'target delete %d' % self.id
        cmd = cmd1 + cmd2
        print('下发移除网关服务器的命令\n', cmd)
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result_out = stdout.read().decode()[:-1]
        result_err = stderr.read().decode()[:-1]
        if result_err != '':
            return result_err + result_out
        #判断删除结果
        for i in range(0, check_times):
            cmd = '''xms-cli -f '{{range .}}{{println .status}}{{end}}' --user %s --password %s target list -q "id.raw:%d"''' \
                  % (temporary_node[3], temporary_node[4], self.id)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            result_out = stdout.read().decode()[:-1]
            result_err = stderr.read().decode()[:-1]
            if result_out == '' and result_err == '':
               #移除对象self
                print('第%d次检查，移除网关服务器成功' %(i+1))
                del self
                break
            if result_out != '':
                time.sleep(check_interval)
                print('第%d次检查，移除网关服务器失败，移除后，网关服务器状态是%s' % ((i+1), result_out))
                i += 1
            elif i == check_times:
                raise delete_target_failed('循环检查结束，删除%d号网关服务器失败' % self.id)


        #移除对象