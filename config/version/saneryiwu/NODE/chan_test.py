import paramiko
from Testbed import testbed
#连接管理节点
# node1 = paramiko.SSHClient()
# # 允许连接不在know_hosts文件中的主
# node1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# # 连接服务器
# node1.connect(hostname=testbed.cluster_manager_ip[0], username=testbed.cluster_node_user, password=testbed.cluster_node_password)
#创建一个交互式SSH连接
node1 = paramiko.Transport(('10.255.101.130',22))
node1.connect(username='root',password='redhat!')
chan=node1.open_session()
chan.settimeout(600)
chan.get_pty()
chan.invoke_shell()
chan.send('ls -l /home/deploy'+'/n')
print(chan.recv(1024))
node1.close()
