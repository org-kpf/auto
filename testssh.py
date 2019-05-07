# coding=utf-8
# from paramiko import SSHClient
# from scp import SCPClient
# ssh = SSHClient()
# ssh.load_system_host_keys()
# ssh.connect('root@10.0.11.122:/home/')
# with SCPClient(ssh.get_transport()) as scp:
#     scp.put(r'‪D:\wiki\autotest\README')
# import subprocess
# import os
# p = subprocess.Popen(["scp", r"‪D:\wiki\autotest\README", "root@10.0.11.122:/root/"])
# sts = os.waitpid(p.pid,1)


from vassal.terminal import Terminal
shell = Terminal(["scp root@10.0.11.122:/home/foo.txt foo_local.txt"])
shell.run()