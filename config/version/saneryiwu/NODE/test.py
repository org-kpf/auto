import paramiko
from Testbed import testbed
import random
import time
volume_list=[]
for i in range(0,0):
    # name = 'volume%d' %i
    # volume_list.append(name)
    print(i)
# print(volume_list)
# print(volume_list[:3])
# print(volume_list[3:])
# class no_available_ip(Exception):
#     pass
# def get_available_ip(cluster):
#     normal_node =  paramiko.SSHClient()
#     normal_node.set_missing_host_key_policy(paramiko.AutoAddPolicy)
#
#     if cluster =='cluster1':
#         ip_list = testbed.cluster1[1]
#         test_user = testbed.cluster1[4]
#         test_password = testbed.cluster1[5]
#         test_admin_user = testbed.cluster1[6]
#         test_admin_password = testbed.cluster1[7]
#     elif cluster =='cluster2':
#         ip_list = testbed.cluster2[1]
#         test_user = testbed.cluster2[4]
#         test_password = testbed.cluster2[5]
#         test_admin_user = testbed.cluster2[6]
#         test_admin_password = testbed.cluster2[7]
#     else:
#         raise no_available_ip('输入集群名称错误')
#     bad_ip_list=[]
#     for a in ip_list:
#         try:
#             normal_node.connect(hostname=a,username=test_user,password=test_password)
#         except:
#             bad_ip_list.append(a)
#     for b in bad_ip_list:
#         ip_list.remove(b)
#     class empty_ip_list(Exception):
#         pass
#     if ip_list==[]:
#         raise empty_ip_list('集群没有可登录的节点')
#     else:
#         return [random.choice(ip_list),test_admin_user,test_admin_password]
# print(get_available_ip('cluster2'))
# def test(a):
#     if a == 'cluster1':
#         print(testbed.cluster1[1])
#     elif a == 'cluster2':
#         print(testbed.cluster2[1])
# test(a='cluster2')