import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import commands

def exe_cmd(cmd):
    status,output = commands.getstatusoutput(cmd)
    print status,output
    return status,output

def sync_data(cmd):
    #os.system(cmd3)
    print cmd3
    out =exe_cmd(cmd)

    print out
    print('sync done')


if __name__ == '__main__':
    cmd1 = r'cd C:\Program Files\PuTTY'
    cmd2 = r'pscp.exe -pw redhat D:\wiki\autotest\README root@10.0.11.126:/home/'
    cmd3 = cmd1 + "&&" + cmd2
    print cmd3

    sync_data(cmd3)

