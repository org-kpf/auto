import paramiko

ip = '10.252.3.136'
port = 22
user = 'root'
passwd = 'redhat'
transport = paramiko.Transport(ip, 22)
transport.connect(username=user,password=passwd)
sftp = paramiko.SFTPClient.from_transport(transport)
sftp.put('1539057330', '/home/tools/fio/1539057330')
transport.close()

