# coding=utf-8
class osd():
    def __init__(self,id,name,data_dir,status,action_status,up,IN,host_id,host_name,pool_id,pool_name,disk_id,disk_device,partition_id,partition_path,osd_id,create):
        self.id = id
        self.name = name
        self.data_dir = data_dir
        self.status = status
        self.action_status = action_status
        self.up = up
        self.IN = IN
        self.host_id = host_id
        self.host_name = host_name
        self.pool_id = pool_id
        self.pool_name = pool_name
        self.disk_id = disk_id
        self.disk_device = disk_device
        self.partition_id = partition_id
        self.partition_path = partition_path
        self.osd_id = osd_id
        self.create = create
    @staticmethod
    def create_osd(disk,cache_partition,read_cache_size,role):
        #disk，必选参数，硬盘的ID，可以用disk的CLI查询出来，取值范围正整数，注意：系统盘加入会报错Disk is already used by root
        #cache_partition,可选参数，缓存盘ID，混合盘场景用SSD创建，取值范围正整数
        #read_cache_size，读缓存大小，不得低于128MB，单位B，128（MB）=134217728（B），例子：134217728
        #role，添加硬盘的角色，取值范围（data|index）二选一，默认data
        if cache_partition == [] and read_cache_size != '':
            cmd = 'osd create --disk %d --read-cache-size %d --role %s' % (disk, read_cache_size, role)
        elif cache_partition == [] and read_cache_size == '':
            cmd = 'osd create --disk %d --role %s' % (disk, role)
        elif cache_partition != [] and read_cache_size == '':
            cmd = 'osd create --disk %d --cache-partition %d --role %s' % (disk, cache_partition, role)
        elif cache_partition != [] and read_cache_size != '':
            cmd = 'osd create --disk %d --cache-partition %d --read-cache-size %d --role %s' % (disk, cache_partition, read_cache_size, role)
        return cmd
    def delete_osd(self,disk_id):
        #命令只能用osd_id来下发，但是为了和创建osd时用的disk_id对应，方便清理环境，所以关键字用disk_id，需要做一个id转化
        cmd = 'osd delete'
        return cmd
