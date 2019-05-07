#! coding:utf-8

def tranIP(ip):
    print ip
    list = ip.split(".")
    list[2] = "110"
    return ("%s.%s.%s.%s") %(list[0],list[1],list[2],list[3])

if __name__=='__main__':
    ip="10.0.11.18"
    test=tranIP(ip)
    print test

