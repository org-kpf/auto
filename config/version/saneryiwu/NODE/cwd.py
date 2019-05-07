import paramiko
from Testbed import testbed
import random
import time
# node1 = paramiko.SSHClient()
# node1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# node1.connect(hostname='10.255.101.130',username='root',password='redhat!',timeout=3600)
# stdin,stdout,stderr = node1.exec_command("xms-cli --user admin --password admin disk list | awk '{print $2,$19}'|grep false | awk '{print $1}'")
# result = stdout.read().decode()[:-1]
# result_list = result.split('\n')
# for i in range(0,len(result_list)):
#     for j in  result_list:
#         result_list.remove(j)
#         result_list.append(int(j))
# print(result_list)
# host = '10.255.101.130'
# port = 22
# user = 'root'
# passwd = 'redhat!'
#
# transport = paramiko.Transport((host, port))
# transport.connect(username=user, password=passwd)
#
# ssh = paramiko.SSHClient()
# ssh._transport = transport
#
# stdin, stdout, stderr = ssh.exec_command('df')
# print(stdout.read().decode())

normal_node = paramiko.SSHClient()
normal_node.set_missing_host_key_policy(paramiko.AutoAddPolicy)
ip_list = testbed.cluster1_admin_ip
bad_ip_list = []
normal_ip_list = []
#从测试床中随机取出ip,登录名和登录密码
#random_ip = random.choice(testbed.cluster_admin_ip)
print('集群IP',ip_list)
for a in ip_list:
    try:
        normal_node.connect(hostname=a, username=testbed.cluster1_node_user, password=testbed.cluster1_node_password, timeout=5)
        time.sleep(3)
        print('尝试来登录 %s' %a)
    except:
        print('登录%s失败了,节点不通' %a)
        bad_ip_list.append(a)
print('连接不通的节点\n', bad_ip_list)
for b in bad_ip_list:
    ip_list.remove(b)
print('正常的节点\n', ip_list)
time.sleep(1)
class empty_ip_list(Exception):
    pass
if ip_list==[]:
    raise empty_ip_list('集群没有可登录的节点')
else:
    print(random.choice(ip_list))
# except IndexError as err:
#     print('集群没有可登录的节点')

