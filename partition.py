# coding=utf-8
class partition():
    def __init__(self,id,uuid,size,path,disk_id,disk_device,create,cluster):
        self.id = id
        self.uuid = uuid
        self.size = size
        self.path = path
        self.disk_id = disk_id
        self.disk_device = disk_device
        self.create = create
        self.cluster = cluster

    @staticmethod
    def create_partition(disk, num):
        '''
        由node对象调用
        :param disk: 指定创缓存分区的SSD盘的ID
        :param num: 一块SSD创建的分区个数
        :return: 给node对象返回拼接的命令
        '''
        cmd = ' partition create --disk=%d --num=%d' % ( disk, num)
        return cmd
